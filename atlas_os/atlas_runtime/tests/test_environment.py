from atlas_runtime import SandboxEnvironment, IOChannel


def test_sandbox_environment_filters_variables(monkeypatch):
    monkeypatch.setenv('FOO', '1')
    monkeypatch.setenv('BAR', '2')
    env = SandboxEnvironment(allowed_variables=['FOO'])
    env.set('EXTRA', '3')
    built = env.build()
    assert built == {'FOO': '1', 'EXTRA': '3'}


def test_io_channel_tracks_stats():
    channel: IOChannel[int] = IOChannel()
    channel.send(1)
    assert channel.receive(timeout=0.1) == 1
    stats = channel.stats()
    assert stats.messages_sent == 1
    assert stats.messages_received == 1
