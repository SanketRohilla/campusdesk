DROP TABLE IF EXISTS comments;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS equipment_loans;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    department TEXT NOT NULL DEFAULT 'General',
    api_token TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    owner_username TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    priority TEXT NOT NULL DEFAULT 'normal',
    status TEXT NOT NULL DEFAULT 'open',
    description TEXT NOT NULL,
    parsed_tags TEXT,
    attachment_name TEXT,
    is_public INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (owner_id) REFERENCES users (id)
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    author_username TEXT NOT NULL,
    author_role TEXT NOT NULL,
    body TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets (id)
);

CREATE TABLE equipment_loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_tag TEXT NOT NULL,
    item_name TEXT NOT NULL,
    borrower_username TEXT NOT NULL,
    serial_number TEXT NOT NULL,
    internal_notes TEXT NOT NULL,
    due_date TEXT NOT NULL
);

-- Seed Users (Passwords stored using SHA-256 hex digest for initial seed)
-- admin -> AdminPass2026!
-- staff_marco -> MarcoSupport99
-- alice -> alice1234
-- bob -> bob56789
INSERT INTO users (username, email, password_hash, role, department, api_token, created_at) VALUES
('admin', 'admin@campusdesk.local', '7c4a8d09ca3762af61e59520943dc26494f8941b', 'admin', 'IT Security & Infrastructure', 'tok_admin_998123_secret', '2026-10-01 08:00:00'),
('staff_marco', 'marco@campusdesk.local', '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8', 'staff', 'Helpdesk Operations', 'tok_staff_441209_internal', '2026-10-02 09:15:00'),
('alice', 'alice.student@campusdesk.local', '7110eda4d09e062aa5e4a390b0a572ac0d2c0220', 'user', 'Computer Science', 'tok_user_alice_1001', '2026-10-05 11:30:00'),
('bob', 'bob.student@campusdesk.local', '8cb2237d0679ca88db6464eac60da96345513964', 'user', 'Data Engineering', 'tok_user_bob_1002', '2026-10-06 14:20:00');

-- Seed Tickets (Includes public community tickets and private internal tickets)
INSERT INTO tickets (owner_id, owner_username, title, category, priority, status, description, parsed_tags, attachment_name, is_public, created_at) VALUES
(3, 'alice', 'Cannot connect to eduroam WiFi in Lab B-204', 'Network', 'high', 'open', 'My laptop keeps dropping the certificate handshake when connecting to the lab access point. Has anyone else in CS had this issue today?', 'room=B204;os=ubuntu24;urgent=true', NULL, 1, '2026-10-20 10:12:00'),
(4, 'bob', 'Requesting USB-C logic analyzer for embedded systems lab', 'Equipment', 'normal', 'in_progress', 'Need a 8-channel logic analyzer until next Friday for our microcontroller assignment.', 'device=analyzer;days=7', NULL, 1, '2026-10-21 15:40:00'),
(1, 'admin', 'INTERNAL: Database backup server credentials rotation', 'Infrastructure', 'critical', 'open', 'Reminder for Marco: staging backup NAS pin is 8492-NAS-ROOT. Do not close until migration to vault is complete.', 'env=prod;restricted=true', 'backup_schedule.txt', 0, '2026-10-22 07:55:00'),
(3, 'alice', 'VPN client configuration error on macOS', 'Software', 'normal', 'resolved', 'Resolved by updating the OpenVPN profile header parameter.', 'os=macos;client=openvpn', NULL, 1, '2026-10-24 13:05:00'),
(2, 'staff_marco', 'Scheduled maintenance notice: Git runner updates', 'Announcement', 'low', 'open', 'All student container runners will restart on Sunday at 02:00 CET. Please push your commits early.', 'service=gitlab;window=sunday', NULL, 1, '2026-10-25 16:00:00');

-- Seed Comments
INSERT INTO comments (ticket_id, author_username, author_role, body, created_at) VALUES
(1, 'staff_marco', 'staff', 'Hi Alice, we are checking the RADIUS certificate on AP-B204. Can you upload your wpa_supplicant log?', '2026-10-20 11:00:00'),
(1, 'bob', 'user', 'I had the exact same problem in B-204 this morning! Switching to the 5GHz SSID worked temporarily.', '2026-10-20 11:45:00'),
(2, 'staff_marco', 'staff', 'Reserved unit #LA-09 at the front desk. Bring your student ID to pick it up.', '2026-10-21 16:10:00'),
(3, 'admin', 'admin', 'Keep this ticket private until the old SSH keys on 10.20.4.15 are revoked.', '2026-10-22 08:10:00');

-- Seed Equipment Loans
INSERT INTO equipment_loans (asset_tag, item_name, borrower_username, serial_number, internal_notes, due_date) VALUES
('MUDT-HW-014', 'Saleae Logic Pro 8', 'bob', 'SN-99481-LP8', 'Checked out by Marco. Deposit waived.', '2026-11-05'),
('MUDT-HW-029', 'Raspberry Pi 5 Kit (8GB)', 'alice', 'SN-44102-RPI5', 'Includes PoE HAT and SD card.', '2026-11-12'),
('MUDT-SEC-002', 'Proxmark3 RDV4 Kit', 'admin', 'SN-00192-PM3', 'Stored in drawer C-3 (PIN: 4910).', '2026-12-01');