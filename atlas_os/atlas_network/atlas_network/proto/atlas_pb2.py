"""Dynamically constructed protobuf definitions for Atlas messages."""

from __future__ import annotations

from google.protobuf import descriptor_pb2, descriptor_pool, message_factory

_pool = descriptor_pool.Default()

file_descriptor = descriptor_pb2.FileDescriptorProto()
file_descriptor.name = "atlas.proto"
file_descriptor.package = "atlas"

# RPCRequest
rpc_request = file_descriptor.message_type.add()
rpc_request.name = "RPCRequest"
field = rpc_request.field.add()
field.name = "method"
field.number = 1
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
field = rpc_request.field.add()
field.name = "payload"
field.number = 2
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_BYTES
field = rpc_request.field.add()
field.name = "correlation_id"
field.number = 3
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

# RPCResponse
rpc_response = file_descriptor.message_type.add()
rpc_response.name = "RPCResponse"
field = rpc_response.field.add()
field.name = "success"
field.number = 1
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_BOOL
field = rpc_response.field.add()
field.name = "payload"
field.number = 2
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_BYTES
field = rpc_response.field.add()
field.name = "correlation_id"
field.number = 3
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

# NodeAnnouncement
node_announcement = file_descriptor.message_type.add()
node_announcement.name = "NodeAnnouncement"
field = node_announcement.field.add()
field.name = "node_id"
field.number = 1
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
field = node_announcement.field.add()
field.name = "host"
field.number = 2
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
field = node_announcement.field.add()
field.name = "port"
field.number = 3
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32

# Heartbeat
heartbeat = file_descriptor.message_type.add()
heartbeat.name = "Heartbeat"
field = heartbeat.field.add()
field.name = "node_id"
field.number = 1
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
field = heartbeat.field.add()
field.name = "timestamp"
field.number = 2
field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
field.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT64

_pool.Add(file_descriptor)
def _get_message(name: str):
    descriptor = _pool.FindMessageTypeByName(name)
    try:
        return message_factory.GetMessageClass(descriptor)
    except AttributeError:  # pragma: no cover - compatibility fallback
        factory = message_factory.MessageFactory()
        return factory.GetPrototype(descriptor)


RPCRequest = _get_message("atlas.RPCRequest")
RPCResponse = _get_message("atlas.RPCResponse")
NodeAnnouncement = _get_message("atlas.NodeAnnouncement")
Heartbeat = _get_message("atlas.Heartbeat")

__all__ = ["RPCRequest", "RPCResponse", "NodeAnnouncement", "Heartbeat"]
