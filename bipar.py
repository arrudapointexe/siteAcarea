import pyautogui
import pyperclip
import time

# 1. Sua lista de códigos (pode vir de um TXT, Excel, etc.)
codigos = [
    3320079495993,
    6060226598904,
    3320043508642,
    3320090491354,
    6052926374865,
    3320031501857,
    3320020509695,
    3320093504125,
    3320061495962,
    3320069492759,
    3320058490517,
    3320089498184,
    3320087503144,
    3320060514447,
    6052426592320,
    3320095501123,
    3320048519919,
    6060226356511,
    3320079498210,
    3320099499288,
    6053026354238,
    3320057501992,
    3320096508381,
    6060226513240,
    3320084501343,
    6060226899007,
    3320010518585,
    3320007511890,
    6060426824633,
    6060426651196
]

print("O bot vai começar em 5 segundos...")
print("👉 Clique no campo onde você quer colar os dados e não mexa o mouse!")
time.sleep(5) # Tempo para você clicar na tela/programa onde quer colar

for codigo in codigos:
    # Copia o texto para a área de transferência do Windows (Ctrl+C virtual)
    pyperclip.copy(codigo)
    
    # Simula o atalho de colar (Ctrl + V)
    pyautogui.hotkey('ctrl', 'v')
    
    # Aperta Enter (se o sistema precisar que aperte Enter para confirmar)
    pyautogui.press('enter')
    
    # Pausa de meio segundo para o sistema não bugar
    time.sleep(1)

print("✅ Bot finalizou a colagem!")