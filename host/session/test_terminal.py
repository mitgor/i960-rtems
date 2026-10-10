import os,pty,termios,unittest
from terminal import Keys,Ticks,Renderer,Terminal,PERIOD
class TerminalTests(unittest.TestCase):
    def test_keys_and_fragmented_arrows(self):
        k=Keys();k.feed(b'a\x1b[',1);k.feed(b'Cd\x1bOA s',2)
        self.assertEqual([k.take() for _ in range(6)],list('addwss'))
        k.feed(b'\x1b[3~\x1b[9999;1z',3);self.assertEqual(k.take(),'')
        k.feed(b'w'*100,4);self.assertEqual(len(k.queue),32);self.assertEqual(k.dropped,68)
        k.feed(b'r',5);self.assertEqual(k.take(),'r');self.assertEqual(k.take(),'')
        k.feed(b'a'*40+b'q',6);self.assertEqual(k.take(),'q');self.assertFalse(k.queue)
    def test_expired_escape_and_interrupt(self):
        k=Keys();k.feed(b'\x1b',0);k.feed(b'a',200_000_000);self.assertEqual(k.take(),'a')
        k.feed(b'\3',300_000_000);self.assertTrue(k.interrupt);self.assertEqual(k.take(),'q')
    def test_wall_clock_ticks_and_cap(self):
        t=Ticks(0);self.assertEqual(t.take(PERIOD//2),0);self.assertEqual(t.take(PERIOD),1)
        self.assertEqual(t.take(PERIOD*25),20);self.assertEqual(t.dropped,4)
        t.reset(PERIOD*50);self.assertEqual(t.take(PERIOD*51),1)
    def test_render_safety_and_diff(self):
        r=Renderer();size=os.terminal_size((80,24));frame=b' '*1920
        first=r.draw(frame,size,'card');self.assertIn(b'\x1b[24;1H',first)
        self.assertEqual(r.draw(frame,size,'card'),b'')
        changed=b'X'+frame[1:];self.assertEqual(r.draw(changed,size,'card'),b'\x1b[1;1H'+changed[:80])
        with self.assertRaises(ValueError):r.draw(b'\x1b'+frame[1:],size,'card')
        small=r.draw(frame,os.terminal_size((40,12)),'card');self.assertIn(b'Resize',small)
        self.assertIn(b'\x1b[2J',r.draw(frame,size,'card'))
    def test_terminal_restore_on_exception(self):
        master,slave=pty.openpty();original=termios.tcgetattr(slave)
        oldin,oldout=os.dup(0),os.dup(1)
        try:
            os.dup2(slave,0);os.dup2(slave,1)
            with self.assertRaises(RuntimeError):
                with Terminal():
                    self.assertNotEqual(termios.tcgetattr(slave),original)
                    raise RuntimeError('render failure')
            restored=termios.tcgetattr(slave)
            # Darwin sets PENDIN itself when canonical processing resumes.
            restored[3]&=~getattr(termios,'PENDIN',0);original[3]&=~getattr(termios,'PENDIN',0)
            self.assertEqual(restored,original)
        finally:os.dup2(oldin,0);os.dup2(oldout,1);os.close(oldin);os.close(oldout);os.close(master);os.close(slave)
if __name__=='__main__':unittest.main()
