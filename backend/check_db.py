import sqlite3

conn = sqlite3.connect('local.db')
cursor = conn.cursor()

print('=== DATABASE TABLES ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
for table in tables:
    print(f'  - {table[0]}')

print('\n=== VOTERS ===')
cursor.execute('SELECT COUNT(*) FROM voters')
voter_count = cursor.fetchone()[0]
print(f'Total voters: {voter_count}')
if voter_count > 0:
    cursor.execute('SELECT epic_id, name, has_voted FROM voters LIMIT 5')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} (voted: {row[2]})')

print('\n=== VOTES ===')
cursor.execute('SELECT COUNT(*) FROM votes')
vote_count = cursor.fetchone()[0]
print(f'Total votes: {vote_count}')

print('\n=== CANDIDATES ===')
cursor.execute('SELECT COUNT(*) FROM candidates')
candidate_count = cursor.fetchone()[0]
print(f'Total candidates: {candidate_count}')
cursor.execute('SELECT candidate_name, party FROM candidates LIMIT 10')
for row in cursor.fetchall():
    print(f'  {row[0]} ({row[1]})')

print('\n=== CHAIN STATUS ===')
cursor.execute('SELECT COUNT(*) FROM blocks')
block_count = cursor.fetchone()[0]
print(f'Chain blocks: {block_count}')

conn.close()
