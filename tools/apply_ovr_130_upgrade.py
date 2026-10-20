#!/usr/bin/env python3
"""Upgrade existing player stats and OVR limits across game data files.

Exact Calibration:
  - Epic: Untrained Level 1 (Box Fresh) = OVR 120-122 -> Trained Max Level = 130 MAX (chưa tính booster)
  - Big Time: Untrained Level 1 (Box Fresh) = OVR 116-118 -> Trained Max Level = 125-126 MAX (chưa tính booster)
  - Show Time: Untrained Level 1 (Box Fresh) = OVR 113-115 -> Trained Max Level = 121-122 MAX (chưa tính booster)
"""
import json
import os
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIGS = {
    'epic': (96, 126),      # Box fresh 120-122 -> Trained 130 MAX (chưa booster)
    'bigtime': (92, 121),   # Box fresh 116-118 -> Trained 125-126 MAX (chưa booster)
    'showtime': (88, 118)   # Box fresh 113-115 -> Trained 121-122 MAX (chưa booster)
}

def scale_val(v, t_min, t_max):
    if v <= 40:
        return v
    # Map original base stat (typically 45-86) to (t_min, t_max)
    t = (v - 45.0) / 41.0
    t = max(0.0, min(1.0, t))
    res = round(t_min + t * (t_max - t_min))
    return min(t_max, max(v, res))

def upgrade_parameters(params, category):
    if not isinstance(params, list) or len(params) < 41:
        return params
    t_min, t_max = CONFIGS.get(category, (94, 124))
    pos = params[0]
    
    if pos == 0:  # GK
        attr_indices = {16, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40}
    else:  # Outfield
        attr_indices = {14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 34, 35, 36, 37, 38, 39, 40}
    
    new_params = list(params)
    for idx in attr_indices:
        if idx < len(new_params):
            new_params[idx] = scale_val(new_params[idx], t_min, t_max)
    return new_params

def main():
    cat_path = os.path.join(ROOT_DIR, 'docs', 'catalog.json')
    with open(cat_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)

    # 1. Map player ID to season category
    player_category = {}
    for pack in catalog.get('packs', []):
        cat = pack.get('category', 'epic')
        for pid in pack.get('player_ids', []):
            player_category[str(pid)] = cat

    print(f"[1/5] Mapped {len(player_category)} existing players to seasons.")

    # 2. Update ZIRU_PLAYER_RECORDS.json (from backup to avoid double-scaling)
    records_files = [
        os.path.join(ROOT_DIR, 'ziru-extra', 'responses', 'ZIRU_PLAYER_RECORDS.json'),
        os.path.join(ROOT_DIR, 'ziru-extra', 'responses', 'ZIRU_PLAYER_RECORDS_DEFAULT.json')
    ]

    for rec_path in records_files:
        backup_path = rec_path + '.bak'
        source_path = backup_path if os.path.exists(backup_path) else rec_path
            
        with open(source_path, 'r', encoding='utf-8') as f:
            records = json.load(f)
            
        updated_count = 0
        for pid, data in records.items():
            cat = player_category.get(str(pid), 'epic')
            gp = data.get('gameplayer', data)
            if 'parameters' in gp:
                gp['parameters'] = upgrade_parameters(gp['parameters'], cat)
                updated_count += 1
                
        with open(rec_path, 'w', encoding='utf-8') as f:
            json.dump(records, f, separators=(',', ':'), ensure_ascii=False)
        print(f"[2/5] Updated {updated_count} player records in {os.path.basename(rec_path)}.")

    # 3. Update CmdUseMyclubAgent.json
    agent_path = os.path.join(ROOT_DIR, 'ziru-extra', 'responses', 'CmdUseMyclubAgent.json')
    agent_bak = agent_path + '.bak'
    agent_source = agent_bak if os.path.exists(agent_bak) else agent_path
    if os.path.exists(agent_source):
        with open(agent_source, 'r', encoding='utf-8') as f:
            agent_data = json.load(f)
            
        def patch_gameplayers(obj):
            if isinstance(obj, dict):
                if 'gameplayer_id' in obj and 'parameters' in obj:
                    pid = str(obj['gameplayer_id'].get('id', ''))
                    cat = player_category.get(pid, 'epic')
                    obj['parameters'] = upgrade_parameters(obj['parameters'], cat)
                for k, v in obj.items():
                    patch_gameplayers(v)
            elif isinstance(obj, list):
                for item in obj:
                    patch_gameplayers(item)
                    
        patch_gameplayers(agent_data)
        with open(agent_path, 'w', encoding='utf-8') as f:
            json.dump(agent_data, f, separators=(',', ':'), ensure_ascii=False)
        print(f"[3/5] Updated box agent templates in {os.path.basename(agent_path)}.")

    # 4. Update docs/catalog.json and docs/catalog.js
    # Load original records from ZIRU_PLAYER_RECORDS.json directly
    main_rec_path = os.path.join(ROOT_DIR, 'ziru-extra', 'responses', 'ZIRU_PLAYER_RECORDS.json')
    with open(main_rec_path, 'r', encoding='utf-8') as f:
        clean_updated_records = json.load(f)
        
    if 'records' in catalog:
        for pid in list(catalog['records'].keys()):
            if pid in clean_updated_records:
                catalog['records'][pid] = clean_updated_records[pid]
                
        with open(cat_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False)
        print(f"[4/5] Updated catalog records in docs/catalog.json.")

        # Update docs/catalog.js
        cat_js_path = os.path.join(ROOT_DIR, 'docs', 'catalog.js')
        with open(cat_js_path, 'w', encoding='utf-8') as f:
            f.write("window.__CATALOG_RAW__ = ")
            json.dump(catalog, f, separators=(',', ':'), ensure_ascii=False)
            f.write(";\n")
        print("[5/5] Re-exported docs/catalog.js for Web Editor.")

    print("\n[SUCCESS] Exact calibration applied: Untrained 120 -> Trained 130 MAX (chua tinh booster)!")

if __name__ == '__main__':
    main()
