import subprocess
import json
import re
import os

PATTERNS = {
    "OpenAI API Key": r"sk-[a-zA-Z0-9]{20,}",
    "Reddit Client Secret": r"pj00TE5ZN4[a-zA-Z0-9_]*",
    "Firebase API Key": r"AIza[0-9A-Za-z\\-_]{35}",
    "Private Key": r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "Generic Password/Secret Assignment": r"(?:api[_-]?key|secret|password|credentials)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
    "Database URL": r"(?:https?://[a-zA-Z0-9.-]+\.firebaseio\.com)"
}

def scan_git_history():
    print("[*] Fetching git log...", flush=True)
    log_cmd = subprocess.run(
        ["git", "log", "--pretty=format:%H|||%an|||%ad|||%s", "--date=short"],
        capture_output=True, text=True, check=True
    )
    commits = log_cmd.stdout.strip().split("\n")
    print(f"[*] Total commits to scan: {len(commits)}", flush=True)
    
    findings = []
    
    for i, line in enumerate(commits, 1):
        if not line:
            continue
        commit_hash, author, date, message = line.split("|||", 3)
        
        # Get diff excluding .venv and package-lock
        diff_cmd = subprocess.run(
            ["git", "show", "--format=", commit_hash, "--", ".", ":(exclude).venv", ":(exclude)*package-lock.json"],
            capture_output=True, text=True, errors="replace"
        )
        diff_text = diff_cmd.stdout
        
        for name, pattern in PATTERNS.items():
            matches = re.finditer(pattern, diff_text, re.IGNORECASE)
            for m in matches:
                start = max(0, m.start() - 60)
                end = min(len(diff_text), m.end() + 60)
                snippet = diff_text[start:end].replace("\n", " ").strip()
                
                findings.append({
                    "commit": commit_hash[:7],
                    "author": author,
                    "date": date,
                    "message": message,
                    "type": name,
                    "match": m.group(0),
                    "context": snippet
                })
        if i % 10 == 0 or i == len(commits):
            print(f"[*] Processed {i}/{len(commits)} commits...", flush=True)
                
    print(f"[+] Total findings: {len(findings)}", flush=True)
    os.makedirs("docs/evidencias/sast", exist_ok=True)
    output_path = os.path.join("docs", "evidencias", "sast", "git_secrets_audit.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)
    print(f"[+] Results saved to {output_path}", flush=True)
    
    seen = set()
    for f in findings:
        key = (f['commit'], f['type'], f['match'])
        if key in seen:
            continue
        seen.add(key)
        print(f"[{f['commit']}] {f['type']} - {f['message']}")
        print(f"    Match: {f['match']}")
        print(f"    Context: {f['context'][:120]}...")
        print("-" * 50)

if __name__ == "__main__":
    scan_git_history()

