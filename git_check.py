import subprocess

with open("git_out.txt", "w") as f:
    res = subprocess.run(["git", "ls-files"], capture_output=True, text=True)
    f.write("TRACKED FILES:\n")
    f.write(res.stdout)
    
    res2 = subprocess.run(["git", "status"], capture_output=True, text=True)
    f.write("\nGIT STATUS:\n")
    f.write(res2.stdout)
    
    res3 = subprocess.run(["git", "log", "-S", "gsk_", "--oneline"], capture_output=True, text=True)
    f.write("\nCOMMITS WITH gsk_:\n")
    f.write(res3.stdout)
