import os
import subprocess

def run():
    print("Running extract.py...")
    # set the PDF directory explicitly just in case
    env = os.environ.copy()
    env["MEDQUEST_PDF_DIR"] = r"C:\dev\MedQuest"
    
    subprocess.run([r".venv\Scripts\python.exe", "extract.py"], env=env, check=True)
    
    print("\nRunning fix_images.py...")
    subprocess.run([r".venv\Scripts\python.exe", "fix_images.py"], check=True)

if __name__ == '__main__':
    run()
