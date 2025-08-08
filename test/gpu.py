import torch

print("CUDA disponible :", torch.cuda.is_available())
print("Nom GPU :", torch.cuda.get_device_name(0))

# Créer un tensor sur GPU
x = torch.randn(1000, 1000, device='cuda')

print("Mémoire GPU allouée (Mo) :", torch.cuda.memory_allocated(0) // 1024**2)
print("Mémoire GPU réservée (Mo) :", torch.cuda.memory_reserved(0) // 1024**2)