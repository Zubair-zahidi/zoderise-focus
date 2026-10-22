import hashlib
import io
import json
import tempfile
import unittest
import zipfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock

from focus.store import Store, LEGACY_TABLES
from focus.planning import next_due
from focus.crypto import encrypt_backup, decrypt_backup


class UpgradeTests(unittest.TestCase):
    def test_encrypted_backup_rejects_non_object_envelopes(self):
        from focus.crypto import MAGIC
        for value in (None, [], 'invalid', 42):
            with self.subTest(value=value), self.assertRaises(ValueError):
                decrypt_backup(MAGIC + json.dumps(value).encode(), 'A long test passphrase')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1791887400.0
        self.db = Store(Path(self.tmp.name) / 'workspace.sqlite3', clock=lambda: self.now)

    def tearDown(self):
        self.tmp.cleanup()

    def test_v1_backup_import_and_v2_roundtrip(self):
        task = self.db.save_task('Keep legacy work')
        snapshot = self.db.snapshot()
        snapshot['format'] = 'zoderise-focus-v1'
        snapshot['tables'] = {k:v for k,v in snapshot['tables'].items() if k in LEGACY_TABLES}
        payload = json.dumps(snapshot).encode()
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as z:
            z.writestr('focus.json', payload)
            z.writestr('manifest.json', json.dumps({'sha256':hashlib.sha256(payload).hexdigest()}))
        self.db.restore(output.getvalue())
        self.assertEqual(self.db.tasks()[0]['id'], task)
        self.assertEqual(self.db.settings()['language'], 'English')
        self.db.save_picks([task])
        self.db.restore(self.db.backup())
        self.assertEqual(self.db.picks()[0]['id'], task)
        self.assertTrue(self.db.settings()['_draft_epoch'])

    def test_dependency_cycle_blocking_and_atomic_save(self):
        a = self.db.save_task('First')
        b = self.db.save_task('Second', prerequisites=[a])
        with self.assertRaises(ValueError):
            self.db.move_task(b, 'Doing')
        with self.assertRaises(ValueError):
            self.db.save_task('Changed', identifier=a, prerequisites=[b])
        self.assertEqual(self.db.get('tasks', a)['title'], 'First')
        self.db.move_task(a, 'Done')
        self.db.move_task(b, 'Doing')
        self.assertEqual(self.db.get('tasks', b)['status'], 'Doing')
        with self.assertRaises(ValueError):
            self.db.set_dependencies(a, [b])

    def test_recurrence_schedules(self):
        self.assertEqual(next_due(date(2026,1,31),'Monthly'), date(2026,2,28))
        self.assertEqual(next_due(date(2026,10,16),'Weekdays'), date(2026,10,19))
        self.assertEqual(next_due(date(2026,10,14),'Selected weekdays',[0,4]), date(2026,10,16))
        self.assertEqual(next_due(date(2026,10,14),'Custom interval',interval=3), date(2026,10,17))
        t = self.db.save_task('Study', due_date=date.today(), recurrence='Selected weekdays', weekdays=[0,4])
        self.db.move_task(t,'Done')
        successor = next(row for row in self.db.tasks() if row['id'] != t)
        self.assertEqual(json.loads(self.db.task_plan(successor['id'])['weekdays']), [0,4])
        self.db.move_task(t,'Next'); self.db.move_task(t,'Done')
        self.assertEqual(len(self.db.tasks()),2)

    def test_board_order_daily_picks_and_planning(self):
        a,b,c = [self.db.save_task(title, status='Next') for title in ('A','B','C')]
        self.db.board_order(a,'Next',c)
        ordered = [t['id'] for t in self.db.tasks()]
        self.assertEqual(ordered[ordered.index(a)+1],c)
        self.db.save_picks([a,b,c])
        with self.assertRaises(ValueError):
            self.db.save_picks([a,b,c,self.db.save_task('D')])
        self.db.set_task_plan(a, date.today())
        self.assertIsNone(self.db.get('tasks',a)['due_date'])
        self.assertEqual(self.db.task_plan(a)['scheduled_day'],date.today().isoformat())

    def test_note_drafts_versions_and_recovery(self):
        note = self.db.save_note('Notes','First')
        self.db.save_draft(note,'Notes','Unsaved typing',note_id=note)
        reopened = Store(self.db.path)
        self.assertEqual(reopened.get('note_drafts',note)['body'],'Unsaved typing')
        self.db.save_note('Notes','Second',identifier=note)
        version = self.db.note_versions(note)[0]
        self.db.restore_note_version(version['id'])
        self.assertEqual(self.db.get('notes',note)['body'],'First')
        self.assertIn('Second',[v['body'] for v in self.db.note_versions(note)])
        self.db.save_note('Whitespace', '    code\n\n', identifier=note)
        self.assertEqual(self.db.get('notes',note)['body'],'    code\n\n')

    def test_templates_and_restore_preview(self):
        project = self.db.apply_template('builtin:Website launch','My website')
        self.assertEqual(len(self.db.tasks(project)),4)
        saved = self.db.save_template(project,'My launch process')
        copy = self.db.apply_template(saved,'Another site')
        self.assertEqual(len(self.db.tasks(copy)),4)
        blob = self.db.backup()
        self.db.save_task('Will be removed')
        row = next(r for r in self.db.backup_preview(blob) if r['Area']=='tasks')
        self.assertEqual(row['Removed'],1)
        self.assertEqual(len(self.db.tasks()),9)

    def test_password_backup_wrong_password_and_tampering(self):
        self.db.save_task('Private task')
        blob = self.db.backup()
        encrypted = encrypt_backup(blob,'A long test passphrase')
        self.assertNotIn(b'Private task', encrypted)
        self.assertEqual(decrypt_backup(encrypted,'A long test passphrase'),blob)
        self.assertNotEqual(encrypt_backup(blob,'A long test passphrase'),encrypted)
        with self.assertRaises(ValueError):
            decrypt_backup(encrypted,'A wrong test passphrase')
        with self.assertRaises(ValueError):
            encrypt_backup(blob,'short')
        self.assertEqual(len(self.db.tasks()),1)

    def test_automatic_backup_retention_and_reminder_dedupe(self):
        task = self.db.save_task('Due task',due_date='2026-01-01')
        self.db.set_settings(backup_interval='Daily', backup_keep=3, reminders=True)
        for _ in range(5):
            self.db.auto_backup(force=True)
        self.assertEqual(len(list((self.db.path.parent/'auto-backups').glob('*.zip'))),3)
        self.db.maintenance(); self.db.maintenance()
        self.assertEqual(len(self.db.alerts()),1)
        self.assertEqual(len(self.db.take_notifications()),1)
        self.assertEqual(len(self.db.take_notifications()),0)
        self.db.start_focus('Finish work',1)
        self.now += 61
        self.db.maintenance()
        self.assertIsNone(self.db.active())
        self.assertEqual(len(self.db.alerts()),2)

    def test_desktop_capture_route(self):
        from focus.desktop import DesktopBridge
        window = Mock()
        bridge = DesktopBridge(window,'http://127.0.0.1:8650')
        bridge.capture()
        window.show.assert_called_once()
        window.load_url.assert_called_once_with('http://127.0.0.1:8650/capture')

    def test_stale_timer_completion_cannot_finish_next_session(self):
        first = self.db.start_focus('First',1)
        self.db.control_focus('complete',first)
        second = self.db.start_focus('Second',1)
        self.assertFalse(self.db.control_focus('complete',first))
        self.assertEqual(self.db.active()['id'],second)


if __name__ == '__main__':
    unittest.main()
