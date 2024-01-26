import json

from google.protobuf.json_format import ParseDict
from google.protobuf.json_format import MessageToDict
import centrifuge.protocol.client_pb2 as protocol


class _JsonCodec:
    """
    _JsonCodec is a default codec for Centrifuge library. It encodes commands using JSON.
    """

    @staticmethod
    def encode_commands(commands):
        return '\n'.join(json.dumps(command) for command in commands)

    @staticmethod
    def decode_replies(data):
        return [json.loads(reply) for reply in data.strip().split('\n')]


def _varint_encode(number):
    """Encode an integer as a varint."""
    buffer = []
    while True:
        towrite = number & 0x7f
        number >>= 7
        if number:
            buffer.append(towrite | 0x80)
        else:
            buffer.append(towrite)
            break
    return bytes(buffer)


def _varint_decode(buffer, position):
    """Decode a varint from buffer starting at position."""
    result = 0
    shift = 0
    while True:
        byte = buffer[position]
        position += 1
        result |= (byte & 0x7f) << shift
        shift += 7
        if not byte & 0x80:
            break
    return result, position


class _ProtobufCodec:
    """
    _ProtobufCodec encodes commands using Protobuf protocol.
    """

    @staticmethod
    def encode_commands(commands):
        serialized_commands = []
        for command in commands:
            # noinspection PyUnresolvedReferences
            serialized = ParseDict(command, protocol.Command()).SerializeToString()
            serialized_commands.append(_varint_encode(len(serialized)) + serialized)
        return b''.join(serialized_commands)

    @staticmethod
    def decode_replies(data):
        replies = []
        position = 0
        while position < len(data):
            message_length, position = _varint_decode(data, position)
            message_end = position + message_length
            message_bytes = data[position:message_end]
            position = message_end
            # noinspection PyUnresolvedReferences
            reply = protocol.Reply()
            reply.ParseFromString(message_bytes)
            replies.append(MessageToDict(reply, preserving_proto_field_name=True))
        return replies
