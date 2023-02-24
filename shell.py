import os
import sys

class Shell:

    def __init__(self):
        self.paths = os.environ["PATH"].split(':') #paths to unix commands + other executables

    def run(self):
        input_prompt = os.environ.get('PS1', '$$$$ ')
        if len(sys.argv) > 1:
            if self.process_file(): return
        while True:
            cmd = input(input_prompt)
            if cmd == 'quit': break
            if cmd == '':
                print('command not recognized')
                continue
            self.process_input(cmd)

    def process_input(self, cmd): #redirects user input to correct place if appropriate
        command = cmd.split(' ')
        linux_cmd_path = self.check_command(command[0])
        if linux_cmd_path != '':
            self.process_unix_command(command, linux_cmd_path)
        elif os.path.exists('./' + command[0]):
            self.process_unix_command(command, './' + command[0])
        elif os.path.exists(command[0]):
            self.process_unix_command(command, command[0])
        else:
            print('command not recognized')

    def check_command(self, dest): #checks self.paths to see if user input had a unix command
        for path in self.paths:
            if os.path.exists(path + '/' + dest):
                return path + '/' + dest
        return ''

    def process_unix_command(self, cmd_list, path): #sends unix command to appropriate method. (redirect, pipa, or runUC)
        args = []
        wait = True
        if cmd_list[-1] == '&': #don't wait for child process to finish
            wait = False
            cmd_list = cmd_list[:-1]
        for i, word in enumerate(cmd_list): # splits input into argument list, redirects to pipa or redirect if needed.
            if word == '>' or word == '<':
                self.redirect(path, cmd_list[:i], cmd_list[i+1:], 0 if word == '<' else 1, wait)
                return
            elif word == '|':
                self.pipa(path, cmd_list[:i], cmd_list[i+1:], wait)
                return
            else:
                args.append(word)
        self.run_unix_command(path, args, wait)

    def run_unix_command(self, path, args, wait): #runs basic unix command. No redirect or pipes.
        if args[0] == 'cd':
            if os.path.exists(args[1]):
                os.chdir(args[1])
            else:
                print('location does not exist')
            return
        pid = os.fork()
        if not pid_check(pid): return
        if pid == 0:
            os.close(2)  # close error file descriptor
            os.execv(path, args)
        if wait: check_status(os.waitpid(pid, 0))

    def redirect(self, cmd_path, cmd1, cmd2, in_out, wait): #runs redirect unix command. Can handle input/output
        pid = os.fork()
        if not pid_check(pid): return
        if pid == 0:
            os.close(2)
            fd = os.open(cmd2[0], os.O_RDWR)
            os.dup2(fd, in_out)
            os.execv(cmd_path, cmd1)
        if wait: check_status(os.waitpid(pid, 0))

    def pipa(self, cmd_path1, cmd1, cmd2, wait): #processes unix command that requires pipe
        cmd_path2 = self.check_command(cmd2[0])
        if cmd_path2 == '': #argument to right of | symbol is not a unix command
            print('second command not recognized')
            return
        r, w = os.pipe() #r = read, w = write
        pid1 = os.fork()
        if not pid_check(pid1): return
        if pid1 == 0:
            os.close(2)
            os.dup2(r, 0)
            os.execv(cmd_path2, cmd2)
        pid2 = os.fork()
        if not pid_check(pid2): return
        if pid2 == 0:
            os.close(2)
            os.dup2(w, 1)
            os.execv(cmd_path1, cmd1)
        os.close(r)
        os.close(w)
        if wait:
            check_status(os.waitpid(pid1, 0))
            check_status(os.waitpid(pid2, 0))

    def process_file(self): #processes file when passed through shell argument
        fd = os.open(sys.argv[1], os.O_RDONLY)
        commands = bytes.decode(os.read(fd, 1000)).split('\n')
        for cmd in commands:
            if cmd == '' or cmd[0] == '#': continue
            if cmd == 'quit' or cmd == 'exit': return True
            print('processing command: ', cmd)
            self.process_input(cmd)
        return False #if file doesn't exit, the code will return to default shell mode

def check_status(code): #checks status code given from os.waitpid() for errors
    if code[1] > 0:
        print('Program terminated: exit code ', code[1])

def pid_check(pid): #checks pid for errors from forking process
    if pid < 0:
        print('fork process failed')
        return False
    return True

if __name__ == "__main__":
    s = Shell()
    s.run()