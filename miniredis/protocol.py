from io import BytesIO

from miniredis.exceptions import CommandError, Disconnect

from collections import namedtuple

#incase something goes wrong we dmade a simple class called error
Error = namedtuple('Error', ('message',))

#maps each wire protocol prefix byte to the method that knows how to pares datatype. this allow the handle_request() function
class ProtocolHandler(object):
    def __init__(self):
        self.handlers = {
            '+': self.handle_simple_string, #simple string
            '-': self.handle_error,         #error message
            ':': self.handle_integer,       #integer
            '$': self.handle_string,        #length-prefixed binary data
            '*': self.handle_array,         #array of other type elements
            '%': self.handle_dict,          #dictionary of key or value pairs
        }

    def handle_request(self, socket_file):
        #grabbing the first byte of the message, the sees which data type it is from the handlers
        first_byte = socket_file.read(1)

        #checks if empty
        if not first_byte:
            raise Disconnect()


        try:
            #converting the byte into plain string
            byte = first_byte.decode('utf-8')
            #goes to whichever handler method that know how to parse this data type
            return self.handlers[byte](socket_file)
        
        #if the first byte is undetictable
        except KeyError:
            raise CommandError('bad request')


    def handle_simple_string(self, socket_file):
        #reading raw bytes up to line ending and decoding into plain text
        line_string = socket_file.readline()
        decoded_string = line_string.decode('utf-8')

        #returning the plain string
        return decoded_string.rstrip('\r\n')


    def handle_error(self, socket_file):
        #reading raw bytes up to line ending and decoding into plain text
        line_string = socket_file.readline()
        decoded_string = line_string.decode('utf-8').rstrip('\r\n')

        #wrapping string in a error namedtuple so the software can reconginze that it is an error from a normal string value
        return Error(decoded_string)


    def handle_integer(self, socket_file):
        #reading raw bytes up to line ending and decoding into plain text
        line_string = socket_file.readline()
        decoded_string = line_string.decode('utf-8').rstrip('\r\n')

        #wrapping decoded string integer so it turns into a real number for example "1234" --> 1234
        return int(decoded_string)


    def handle_string(self, socket_file):
        #checking for the length of the string 
        length_line = socket_file.readline()
        length = int(length_line.decode('utf-8').rstrip('\r\n'))

        #ccheking if the length of the string is -1 if so we return none as -1 means no value
        if length == -1:
            return None

        #reads the actual value and returns the string with the last two character sliced off which are \r\n
        return (socket_file.read(length + 2))[:-2]

    def handle_array(self, socket_file):
        #checking for the length of the array
        length_el_line = socket_file.readline()
        length_el = int(length_el_line.decode('utf-8').rstrip('\r\n'))

        # array has mulitple data types each element containing its own byte we can call the handle request to parse each of them
        #this would also handle nested arrays as well since handle_request would call handle_array or handle_dict again
        return [self.handle_request(socket_file) for _ in range(length_el)]

    def handle_dict(self, socket_file):
        #checking for the length of the array
        length_el_line = socket_file.readline()
        length_el = int(length_el_line.decode('utf-8').rstrip('\r\n'))

        #since there is 1 key paired with 1 value it means we need to read twice as many elements
        length_total = length_el * 2

        # since the dict is written as (key, value, key, value,.....) each with its own prefic byte, we can reuse 
        #handl_request to parse each on recursivly
        elements =  [self.handle_request(socket_file) for _ in range(length_total)]

        #zip helps pair up every even index which is the key with every odd-index which is the value
        #while dic constructs the final dict
        return dict(zip(elements[::2], elements[1::2]))


    from io import BytesIO

    def write_response(self, socket_file, data):
        #bulding the entire serialized response in memory this matters for nested
        #arrays or dict, where we would we otherwise make many small, slow writes to the network
        buf = BytesIO()

        #delegate to _write, which will inspect the type of data and recusively
        #serialize into a buf, ex. handling nested lists/dicts.
        self._write(buf, data)

        #moving to the start of the buffer so we can read everything thats written
        #instead of where the cursor remained
        buf.seek(0)

        #sending the built response back to the user, along with flushing it to make sure 
        # it is actually sent over the network rather than remain in an internal buffer.
        socket_file.write(buf.getvalue())
        socket_file.flush()


    def _write(self, buf, data):

        #this is a seperate if branch made to convert the data from string to bytes, so
        # both the regular trings and raw bytes get handled identically by the flow blocks below
        if isinstance(data, str):
            data = data.encode('utf-8')

        #binary-safe string type ($), structure: a length prefixed line, followed with the raw data, and followed 
        #by trailing \r\n.
        if isinstance(data, bytes):

            #writes the header line "$<length>\r\n"
            buf.write(('$%s\r\n' % len(data)).encode('utf-8'))
            #write the acutal data
            buf.write(data)
            #write the trailing line ending
            buf.write(b'\r\n')

        #integer type (:) only prefix, the number and the line ending no length_prefixing
        #needed since int do not contain \r\n
        elif isinstance(data, int):
            buf.write((':%s\r\n' % data).encode('utf-8'))

        #error type (-) format is just prefix and the message text on one line, no length prefix
        #data.message is used to pull actual text from error namedtuple
        elif isinstance(data, Error):
            buf.write(('-%s\r\n' % data.message).encode('utf-8'))

        #array type (*) wire format is the '*' prefix + element count, followed by each element written out in its own
        #full wire fomat
        elif isinstance(data, (list, tuple)):

            #write the "*<count>\r\n" header line
            buf.write(('*%s\r\n' % len(data)).encode('utf-8'))

            #recursivley writes each item into the sam buffer. if item iteself is list or dict
            #it reenters _write and hits the matching branch
            for item in data:
                self._write(buf, item)

        #dict type (%) wire format is the '%' prefix + number of key_value PAIRS, followed by each key followed by its value
        #each written in its own full wire format
        elif isinstance(data, dict):

            #writes "%<pair count>\r\n" header line
            #since '%' is python formatting place holder, '%%' to produce one literal '%' in the output
            #then '%s' as the actual placehodler for len(data)
            buf.write(('%%%s\r\n' % len(data)).encode('utf-8'))

            #for each key it recusiviley write the key then immediately writes its matching value
            #right after same idea as the list branch
            for key in data:
                self._write(buf, key)
                self._write(buf, data[key])

        #NULL/None case resue '$' with a length of -1 meaning no value at all
        elif data is None:
            buf.write(('$-1\r\n').encode('utf-8'))
