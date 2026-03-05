import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib

dataset = pd.read_csv('date_perfecte.csv')
X = dataset['Text_Complet'].astype(str)
y = dataset['Score'].astype(float) 

# Scikit-Learn (TF-IDF): NLP Feature Extraction
# Transformam cuvintele (string) in vectori matematici (numere). Pastram doar cele mai importante 15.000 cuvinte.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
vectorizator = TfidfVectorizer(max_features=15000, stop_words='english')

X_train_sparse = vectorizator.fit_transform(X_train)
X_test_sparse = vectorizator.transform(X_test)

# PyTorch Dataset: Optimizare Memorie (Lazy Loading)
# Aceasta clasa este cruciala: in loc sa incarcam toata matricea uriasa in RAM (ceea ce ar da crash PC-ului),
# incarcam doar "bucati" (batches) exact cand reteaua are nevoie de ele.
class RecenziiDataset(Dataset):
    def __init__(self, date_x, date_y):
        self.X = date_x
        self.y = date_y.values

    def __len__(self):
        return self.X.shape[0]

    def __getitem__(self, idx):
        x_dens = torch.FloatTensor(self.X[idx].toarray().squeeze())
        y_tensor = torch.FloatTensor([self.y[idx]])
        return x_dens, y_tensor

dataset_train = RecenziiDataset(X_train_sparse, y_train)
loader = DataLoader(dataset_train, batch_size=256, shuffle=True)

# PyTorch nn.Module: Arhitectura Feed-Forward Neural Network (MLP)
class DropshipNet(nn.Module):
    def __init__(self):
        super(DropshipNet, self).__init__()
        # Stratul de intrare primeste 15000 de features si le comprima in 256 neuroni
        self.stratul_ascuns = nn.Linear(15000, 256) 
        self.activare = nn.ReLU() # Functie de activare non-liniara
        self.stratul_iesire = nn.Linear(256, 1) # Output: un singur numar (Scorul final)

    def forward(self, x):
        x = self.stratul_ascuns(x)
        x = self.activare(x)
        x = self.stratul_iesire(x)
        return x

model = DropshipNet()

# Optimizare matematica: MSE (Mean Squared Error) si Adam Optimizer
criteriu_pierdere = nn.MSELoss()
optimizator = optim.Adam(model.parameters(), lr=0.001) 

# Antrenament
epoci = 5 

for epoca in range(epoci):
    pierdere_totala = 0
    
    for batch_x, batch_y in loader:
        optimizator.zero_grad() # Resetam gradientii
        predictii = model(batch_x) # Reteaua incearca sa ghiceasca scorul
        pierdere = criteriu_pierdere(predictii, batch_y) # Calculam cat de mult a gresit
        pierdere.backward() # Backpropagation (invata din greseala)
        optimizator.step() # Actualizam ponderile neuronilor
        pierdere_totala += pierdere.item()
        
    print(f"🔄 Epoca {epoca+1}/{epoci} | Eroare (Loss): {pierdere_totala/len(loader):.4f}")

# Serializarea (Salvarea) modelului pentru a fi folosit in productie de API
torch.save(model.state_dict(), 'retea_dropshipping.pth')
joblib.dump(vectorizator, 'vocabular_nn.pkl')