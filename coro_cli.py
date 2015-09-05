from ubinascii import hexlify, unhexlify

from async_pyb import new_event_loop, set_event_loop, \
    Future, TimeoutError, \
    coroutine, sleep, wait_for, GetRunningLoop

import pyb
import gc

from pyb import USB_VCP, SPI, Pin, millis, elapsed_millis


class GotEOT(Exception):
    pass

class CoroCLI():

    def __init__(self, role):
        self.role = role
        self.console = USB_VCP()
        self.command_dispatch = { }
        self.cmd_hist = [b'']
        self.prompt = bytes(self.role + '> ', 'ASCII')
        self.tx_want_ack = True
        self.destination = bytes(8)


    @coroutine
    def readline(self):
        console = self.console
        hi = 0
        buf = b''
        while console.isconnected():
            if console.any():
                c = console.read(1)
                if c == b'\x04':
                    raise GotEOT
                elif c == b'\x0e': # ^N
                    buf = self.cmd_hist[hi][:]
                    hi = max(hi-1, 0)
                    console.write(b'\r' + self.prompt + buf + b'\x1b[K')
                elif c == b'\x10': # ^P
                    buf = self.cmd_hist[hi][:]
                    hi = min(hi+1, len(self.cmd_hist)-1)
                    console.write(b'\r' + self.prompt + buf + b'\x1b[K')
                elif c == b'\r' or c == b'\n':
                    if buf and buf != self.cmd_hist[0]:
                        self.cmd_hist.insert(0, buf)
                    if len(self.cmd_hist) > 16:
                        self.cmd_hist.pop()
                    hi = 0
                    console.write(b'\r\n')
                    return buf
                else:
                    buf += c
                    console.write(c)
            else:
                yield from sleep(50)

    @coroutine
    def write(self, buf):
        self.console.write(buf)
        yield

    @coroutine
    def writeln(self, buf):
        yield from self.write(buf)
        yield from self.write(b'\r\n')


    @coroutine
    def interpret(self, line):
        if not line:
            return

        cmd, _, rol = line.lstrip().partition(b' ')
        cmd = str(cmd, 'ASCII')
        rol = rol.lstrip()

        fun = self.command_dispatch.get(cmd.lower())
        if fun:
            yield from fun(self, cmd, rol)
        elif cmd in ('help', '?'):
            yield from self.write('Commands are: ')
            yield from self.writeln(', '.join(sorted(self.command_dispatch.keys())))
        else:
            yield from self.writeln('huh?')


    @coroutine
    def repl(self, noquit=False):
        console = self.console
        while(console.isconnected()):
            #console.self.write(prompt)
            yield from self.write(self.prompt)
            try:
                line = yield from self.readline()
                yield from self.interpret(line)
            except GotEOT:
                if noquit:
                    yield from self.writeln("can't quit!")
                else:
                    return


################################################################
'''
@coroutine
def info_cmd(cli, cmd, rol):

    @coroutine
    def showAT(at):
        yield from cli.write(' %s %d' % (at, (yield from cli.xb.AT_cmd(at))))

    yield from cli.write('addr %s' % hexlify(cli.xb.address))
    yield from showAT('DB')
    yield from showAT('PL')
    loop = yield GetRunningLoop(None)
    yield from cli.write(' qlen %d' % len(loop.q))
    gc.collect()
    yield
    gc.collect()
    yield from cli.write(' mem_free %d' % gc.mem_free())
    yield from cli.writeln('')


@coroutine
def at_cmd(cli, cmd, rol):
    print(repr(rol))
    try:
        v = yield from cli.xb.AT_cmd(rol[:2], rol[2:])
    except ATStatusError as e:
        yield from cli.writeln(e.args[0])
    else:
        yield from cli.writeln(repr(v))

@coroutine
def echo_cmd(cli, cmd, rol):
    args = rol.split()
    if args and args[0] == b'-q':
        quiet = True
        args.pop(0)
    else:
        quiet = False
    try:
        n = int(args[0])
    except:
        n = 1<<30
    yield from cli.echoServer(n, quiet=quiet)


@coroutine
def dest_cmd(cli, cmd, rol):
    # Set a default destination address
    if len(rol):
        cli.destination = unhexlify(rol)
    else:
        yield from cli.writeln(hexlify(cli.destination))
'''

@coroutine
def coro_cmd(cli, cmd, rol):
    # launch a command in the background, as a coro
    c_cmd, _, c_rol = rol.partition(b' ')
    c_cmd = str(c_cmd, 'ASCII')
    c_rol = c_rol.lstrip()

    fun = cli.command_dispatch.get(c_cmd.lower())
    #print(cli, c_cmd, c_rol)
    if fun:
        yield fun(cli, c_cmd, c_rol)
    else:
        yield from cli.writeln("coro can't find %s" % c_cmd)


'''
@coroutine
def ping_cmd(cli, cmd, rol):
    args = rol.split()

    if args and args[0] == b'-q':
        quiet = True
        args.pop(0)
    else:
        quiet = False

    try:
        n = int(args[0])
    except:
        n = 1

    try:
        address = unhexlify(args[1])
    except:
        address = cli.destination

    loop = yield GetRunningLoop(None)

    t0 = millis()
    for i in range(n):
        payload = b'%d: ping at %.3f' % (i+1, loop.time())
        status = yield from wait_for((yield from cli.xb.tx(payload, address, ack=cli.tx_want_ack)))
        if not quiet:
            yield from cli.write('-')
        try:
            a, d = yield from wait_for(cli.xb.rx(), 1)
        except TimeoutError:
            yield from cli.write('X')
        else:
            if not quiet:
                yield from cli.write('|')

    duration = elapsed_millis(t0)
    yield from cli.writeln('')
    yield from cli.writeln("%d in %dms" % (n, duration))


@coroutine
def rx_cmd(cli, cmd, rol):
    args = rol.split()

    try:
        n = int(args[0])
    except:
        n = 1

    try:
        timeout = float(str(args[1], 'ASCII'))
    except:
        timeout = None

    print(n, timeout)
    for i in range(n):
        try:
            a, d = yield from wait_for(cli.xb.rx(), timeout)
        except TimeoutError:
            yield from cli.writeln("timeout")
        else:
            yield from cli.writeln('from %s got %r' % \
                                   (str(hexlify(a), 'ASCII'), d))

@coroutine
def tx_cmd(cli, cmd, rol):
    addr, _, payload = rol.partition(b':')
    if len(addr) == 16:
        address = unhexlify(addr)
    else:
        address = cli.destination
    yield from cli.write('sending %d bytes to %r...' % \
                       (len(payload), address))
    status = yield from wait_for((yield from cli.xb.tx(payload, address, ack=cli.tx_want_ack)))
    yield from cli.writeln('status %r' % status)


@coroutine
def ack_cmd(cli, cmd, rol):
    if len(rol):
        cli.tx_want_ack = rol == b'on'
    else:
        yield from cli.writeln(cli.tx_want_ack and 'on' or 'off')
'''

@coroutine
def eval_cmd(cli, cmd, rol):
    d = {'cli': cli,
         'loop': (yield GetRunningLoop(None)),
         'pyb': pyb }
    try:
        v = eval(rol, d)
    except Exception as e:
        v = e
    yield from cli.writeln(repr(v))

@coroutine
def exec_cmd(cli, cmd, rol):
    d = {'cli': cli,
         'loop': (yield GetRunningLoop(None)),
         'pyb': pyb }
    try:
        v = exec(rol, d)
    except Exception as e:
        v = e
    yield from cli.writeln(repr(v))

@coroutine
def quit_cmd(cli, cmd, rol):
    raise GotEOT
    yield


@coroutine
def heyUsaid_cmd(cli, cmd, rol):
    yield from cli.writeln("You said %s %s" % (cmd, rol))


def inject_standard_commands(cli):
    cli.command_dispatch.update({
        'coro': coro_cmd,
        'eval': eval_cmd,
        'exec': exec_cmd,
        'hey': heyUsaid_cmd,
        'quit': quit_cmd })


def interact(role=None):

    cli = CoroCLI('pre-alpha')

    inject_standard_commands(cli)

    loop = new_event_loop()
    set_event_loop(loop)
    loop.run_until_complete(cli.repl())

if __name__ == '__main__':
    interact()
