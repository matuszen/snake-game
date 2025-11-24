


### **setup.sh**

#!/bin/bash
# Skrypt instalacyjny dla Snake Game Viewer (Python + C++)

echo "Instalacja wymaganych bibliotek Python..."
pip3 install --user "numpy>=1.24.0" "posix-ipc>=1.1.0" "pygame>=2.1"

echo "Sprawdzenie instalacji..."
python3 -m pip show numpy posix_ipc pygame

echo "Gotowe! Możesz teraz uruchomić grę:"
echo "python3 main.py"