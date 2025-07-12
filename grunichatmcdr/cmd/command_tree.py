from mcdreforged.api.all import *

def register_grunichat_command(server, ws_service, config):
    # !!grunichat rename <new_id>
    rename_branch = Literal('rename').then(Text('new_id').runs(lambda src, ctx: ws_service.rename(src, ctx['new_id'])))
    # !!grunichat reconnect
    reconnect_branch = Literal('reconnect').runs(lambda src, ctx: ws_service.reconnect(src))
    # !!grunichat disconnect
    disconnect_branch = Literal('disconnect').runs(lambda src, ctx: ws_service.disconnect(src))
    # !!grunichat connect <url>
    connect_branch = Literal('connect').then(Text('url').runs(lambda src, ctx: ws_service.connect(src, ctx['url'])))

    tree = (
        Literal('!!grunichat')
        .runs(lambda src, ctx: src.reply('§a[GRUniChat] 用法: !!grunichat <rename|reconnect|disconnect|connect> [参数]'))
        .then(rename_branch)
        .then(reconnect_branch)
        .then(disconnect_branch)
        .then(connect_branch)
    )
    server.register_command(tree)
