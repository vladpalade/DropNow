import torch
import torch.nn as nn
import joblib

class DropshipNet(nn.Module):
    def __init__(self):
        super(DropshipNet, self).__init__()
        self.stratul_ascuns = nn.Linear(15000, 256) 
        self.activare = nn.ReLU()
        self.stratul_iesire = nn.Linear(256, 1)

    def forward(self, x):
        x = self.stratul_ascuns(x)
        x = self.activare(x)
        x = self.stratul_iesire(x)
        return x

try:
    vectorizator = joblib.load('vocabular_nn.pkl')
    model = DropshipNet()
    model.load_state_dict(torch.load('retea_dropshipping.pth', weights_only=True))
    model.eval()
except: pass

def analizeaza_recenzii(lista_recenzii):
    if not lista_recenzii:
        return 0.0, []

    scoruri_individuale = []
    
    for text in lista_recenzii:
        if not text.strip(): continue
        text_transformat = vectorizator.transform([text])
        tensor_intrare = torch.FloatTensor(text_transformat.toarray())
        
        with torch.no_grad():
            nota = model(tensor_intrare).item()
            
        nota_finala = max(1.0, min(5.0, nota))
        scoruri_individuale.append((text, nota_finala))

    media = sum([s[1] for s in scoruri_individuale]) / len(scoruri_individuale)
    
    # Sortam recenziile in functie de cat de aproape sunt de medie
    scoruri_individuale.sort(key=lambda x: abs(x[1] - media))
    
    # Extragem doar textele celor mai bune 3
    top_3_recenzii = [s[0] for s in scoruri_individuale[:3]]
    
    return round(media, 2), top_3_recenzii