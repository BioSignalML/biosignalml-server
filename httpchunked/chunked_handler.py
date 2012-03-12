"""
Tornado chunked data handler from https://gist.github.com/753992
"""

from tornado import web

from iostream_callback import (
    Callback,
    Data,
    DONE,
)

from cStringIO import StringIO

WAIT_LENGTH = (1, )
WAIT_CHUNK = (2, )


class ChunkedData(Data):

    def __init__(self):
        self.chunk = StringIO()
        self.chunk_length = 0

        super(ChunkedData, self).__init__()


class LengthCallback(Callback):
    start_state = WAIT_LENGTH

    def _handle(self, data):
        assert data[-2:] == '\r\n', "chunk size ends with CRLF"
        self.data.chunk_length = int(data[:-2], 16)

        if self.data.chunk_length:
            self.data.state = WAIT_CHUNK
        else:
            self.data.state = DONE


class DataCallback(Callback):
    start_state = WAIT_CHUNK

    def _handle(self, data):
        assert data[-2:] == '\r\n', "chunk data ends with CRLF"
        self.data.chunk.write(data[:-2])

        self.data.state = WAIT_LENGTH


class ChunkReader(object):
    def __init__(self, handler):
        self.handler = handler

        stream = handler.request.connection.stream

        data = ChunkedData()
        func = Callback.make_entry_callback(data, (
                LengthCallback(data,
                    lambda self: stream.read_until('\r\n', self)),
                DataCallback(data,
                    lambda self: stream.read_bytes(data.chunk_length + 2, self)),
            ), self._done_callback)

        data.state = WAIT_LENGTH
        func()

    def _done_callback(self, data):
        self.handler._on_chunks(data.chunk)


class ChunkedHandler(web.RequestHandler):
    def _handle_chunked(self, *args, **kwargs):
        # we assume that the wrapping server has not sent/flushed the
        # 100 (Continue) response
        if self.request.headers.get('Expect', None) == '100-continue' and \
            not 'Content-Length' in self.request.headers and \
            self.request.headers.get('Transfer-Encoding', None) == 'chunked':

            self._auto_finish = False
            ChunkReader(self)

            self.request.write("HTTP/1.1 100 (Continue)\r\n\r\n")

            return True
        return False

    def _on_chunks(self, all_chunks):
        self.finish()
