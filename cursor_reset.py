import os, json, uuid, subprocess, shutil
from pathlib import Path
from datetime import datetime

class CursorReset:
    def __init__(self):
        self.home = Path.home()
        self.cursor_support = self.home / "Library" / "Application Support" / "Cursor"
        self.cursor_hidden = self.home / ".cursor"
    
    def print_header(self):
        print("\n" + "="*60)
        print("🔧 CURSOR RESET TOOL - MACOS")
        print("="*60 + "\n")
    
    def step1_kill(self):
        print("[1/5] Encerrando Cursor...")
        subprocess.run(["pkill", "-9", "Cursor"], capture_output=True)
        subprocess.run(["pkill", "-9", "cursor"], capture_output=True)
        print("✅ Cursor encerrado\n")
    
    def step2_delete(self):
        print("[2/5] Deletando configurações...")
        paths = [self.cursor_support, self.cursor_hidden, self.home / ".cursor.json"]
        for p in paths:
            if p.exists():
                shutil.rmtree(p) if p.is_dir() else p.unlink()
                print(f"✅ Deletado: {p.name}")
        print()
    
    def step3_reset(self):
        print("[3/5] Resetando Machine IDs...")
        storage = self.cursor_support / "User" / "globalStorage" / "storage.json"
        storage.parent.mkdir(parents=True, exist_ok=True)
        
        ids = {
            "telemetry.machineId": uuid.uuid4().hex,
            "telemetry.macMachineId": uuid.uuid4().hex,
            "telemetry.devDeviceId": str(uuid.uuid4()),
        }
        storage.write_text(json.dumps(ids, indent=2))
        print("✅ IDs resetados\n")
    
    def step4_perms(self):
        print("[4/5] Ajustando permissões...")
        for p in [self.cursor_support, self.cursor_hidden]:
            if p.exists():
                os.chmod(p, 0o755)
        print("✅ Permissões ajustadas\n")
    
    def step5_done(self):
        print("[5/5] Concluído!")
        print("""
✅ RESET COMPLETO!

Próximos passos:
1️⃣  Abra Cursor novamente
2️⃣  Use um EMAIL NOVO (não o anterior!)
3️⃣  Divirta-se com a versão de teste!
        """)
    
    def run(self):
        self.print_header()
        self.step1_kill()
        self.step2_delete()
        self.step3_reset()
        self.step4_perms()
        self.step5_done()

if __name__ == "__main__":
    CursorReset().run()
