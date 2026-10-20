import json
import glob
import os

stats = ['possession', 'short_counter', 'long_ball', 'long_counter', 'side_attack', 'overload']

files_updated = 0
coaches_updated = 0

for filepath in glob.glob('ziru-extra/responses/*.json'):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        continue

    changed = False

    def boost_coach(c):
        global coaches_updated
        if not isinstance(c, dict):
            return
        modified = False
        for s in stats:
            if c.get(s) != 99:
                c[s] = 99
                modified = True
        if modified:
            coaches_updated += 1

    # Check top-level coach_list
    if isinstance(data, dict):
        if 'coach_list' in data and isinstance(data['coach_list'], list):
            for c in data['coach_list']:
                boost_coach(c)
                changed = True

        if 'market_coach_list' in data and isinstance(data['market_coach_list'], list):
            for c in data['market_coach_list']:
                boost_coach(c)
                changed = True

        # Check entry_info
        ei = data.get('entry_info')
        if isinstance(ei, dict):
            if 'coach_list' in ei and isinstance(ei['coach_list'], list):
                for c in ei['coach_list']:
                    boost_coach(c)
                    changed = True
            if 'squad_list' in ei and isinstance(ei['squad_list'], list):
                for sq in ei['squad_list']:
                    sd = sq.get('squad_data')
                    if isinstance(sd, dict):
                        coaches = sd.get('coach')
                        if isinstance(coaches, list):
                            for c in coaches:
                                boost_coach(c)
                                changed = True

        # Check squad_data at root
        sd = data.get('squad_data')
        if isinstance(sd, dict):
            coaches = sd.get('coach')
            if isinstance(coaches, list):
                for c in coaches:
                    boost_coach(c)
                    changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        files_updated += 1
        print(f"Boosted coaches in: {os.path.basename(filepath)}")

print(f"\nDone! Updated {coaches_updated} coach instances across {files_updated} response files.")
