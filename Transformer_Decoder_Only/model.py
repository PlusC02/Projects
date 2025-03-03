# -*- coding: utf-8 -*-
"""model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1F0asdbbBR-5boKJdSjvU7GtGfxlh_Deh
"""

import torch
import torch.nn as nn
from torch.nn import functional as F
import tiktoken # Make sure you have installed tiktoken

from LayerNorm import LayerNorm
from MaskedMultiheadAttention import Masked_MultiHeadAttention
from NeuralNetwork import Position_wise_FFN
from Block import decoder_block

#Hyperparameter
batch_size = 64 # how many independent sequences will we process in parallel?
sequence_len = 128 # what is the maximum context length for predictions?
learning_rate = 3e-4
device = 'cuda' if torch.cuda.is_available() else 'cpu'
embed_dim = 256 # Make sure embed_dim % num_head == 0 and embed_dim is even number
num_head = 4
num_layer = 6
dropout = 0.2
eval_interval = 50

#wget https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt

with open('input.txt','r') as f:
  text = f.read()

data = text
index = int(0.9*len(data))

#Tokenizer
enc = tiktoken.get_encoding("cl100k_base")
assert enc.decode(enc.encode("hello world")) == "hello world" # A checking

#Additional label encoder to reduce the vocab_size
label_encode = { token:i for i,token in enumerate(sorted(list(set(enc.encode(data)))))}
label_decode = { i:token for i,token in enumerate(sorted(list(set(enc.encode(data)))))}

#Lambda function
encode = lambda s: [label_encode[c] for c in s] # encoder: take a string, output a list of integers
decode = lambda l: ''.join([label_decode[i] for i in l]) # decoder: take a list of integers, output a string

train = data[:index]
test = data[index:]
vocab_size = len(set(enc.encode(data))) # A parameter used later Without label encoder size = 100252 while 12111 now
train_data = torch.tensor( encode( enc.encode(train) ), dtype = torch.long)
test_data = torch.tensor( encode( enc.encode(test) ) , dtype = torch.long)

class Generative_model_with_attn(nn.Module): ## Would be using global variable
  # Refer to https://www.youtube.com/watch?v=kCc8FmEb1nY&t=5716s
  # This deviates from the default way but suffices for testing the component
  """
  Final model that integrate with all component
  Embedding
  Positional Encoding
  6 identical block
  Layer Norm
  Linear

  """
  def __init__(self, vocab_size,sequence_len,embed_dim,dropout,num_head, num_layer):
    super().__init__()
    self.token_embed_table = Embedding(vocab_size,embed_dim)
    self.position_enc = Positional_Encoding(embed_dim, sequence_len, dropout)
    self.blocks = nn.Sequential(*[decoder_block(embed_dim, num_head,dropout) for _ in range(num_layer)])
    self.layerNorm = LayerNorm(embed_dim)
    self.linear = nn.Linear(embed_dim,vocab_size)

    self.apply(self._init_weights)

    self.sequence_len = sequence_len

  def _init_weights(self,module):
    if isinstance(module,nn.Linear):
      torch.nn.init.normal_(module.weight,mean = 0.0, std = 0.02)
      if module.bias is not None:
        torch.nn.init.zeros_(module.bias)
    elif isinstance(module, nn.Embedding):
      torch,nn.init.normal_(module.weight, mean = 0.0, std = 0.02)


  def forward(self,x,targets = None): # if target exist, we want to train it
    Batch, Sequence_len = x.shape

    #
    token_x = self.token_embed_table(x) # B,S,D
    x = self.position_enc(token_x) # positional encode has done x + positional encoding
    x = self.blocks(x)
    x = self.layerNorm(x)
    logits = self.linear(x) # B,S,vocab_size

    if targets is None:
        loss = None
    else:
        B, T, C = logits.shape
        logits = logits.view(B*T, C)
        targets = targets.view(B*T)
        loss = F.cross_entropy(logits, targets)

    return logits, loss


    def generate(self, idx, max_new_tokens):
      # idx is (B, T) array of indices in the current context
      for _ in range(max_new_tokens):
          # crop idx to the last block_size tokens
          idx_cond = idx[:, -self.sequence_len:]
          # get the predictions
          logits, loss = self(idx_cond)
          # focus only on the last time step
          logits = logits[:, -1, :] # becomes (B, vocab_size)
          # apply softmax to get probabilities
          probs = F.softmax(logits, dim=-1) # (B, vocab_size)
          # sample from the distribution
          idx_next = torch.multinomial(probs, num_samples=1) # (B, 1)
          # append sampled index to the running sequence
          idx = torch.cat((idx, idx_next), dim=1) # (B, T+1)
      return idx

# data loading
def get_batch(split):
    # generate a small batch of data of inputs x and targets y
    data = train_data if split == 'train' else test_data
    ix = torch.randint(len(data) - sequence_len, (batch_size,))
    x = torch.stack([data[i:i+sequence_len] for i in ix])
    y = torch.stack([data[i+1:i+sequence_len+1] for i in ix])
    x, y = x.to(device), y.to(device)
    return x, y

@torch.no_grad()
def estimate_loss():
    out = {}
    model.eval()
    for split in ['train', 'val']:
        losses = torch.zeros(eval_interval)
        for k in range(eval_interval):
            X, Y = get_batch(split)
            logits, loss = model(X, Y)
            losses[k] = loss.item()
        out[split] = losses.mean()
    model.train()
    return out

def train(max_iter = 1000, eval_interval = 50 ,save_interval = 10, model_weight_path = None): #https://pytorch.org/tutorials/beginner/basics/saveloadrun_tutorial.html
  if model_weight_path is not None:
    model.load_state_dict(torch.load(model_weight_path))
  for i in range(max_iter):
    if i % save_interval == 0 or i ==i == max_iter - 1:
      torch.save(model.state_dict(), 'model_weights.pth')
    if i % eval_interval == 0 or i == max_iter - 1:
      losses = estimate_loss()
      print(f"step {i}: train loss {losses['train']:.4f}, val loss {losses['val']:.4f}")

    # sample a batch of data
    xb, yb = get_batch('train')

    # evaluate the loss
    logits, loss = model(xb, yb)
    optimizer.zero_grad(set_to_none=True)
    loss.backward()
    optimizer.step()

model = Generative_model_with_attn(vocab_size,sequence_len,embed_dim,dropout,num_head,num_layer)
m = model.to(device)
# print the number of parameters in the model
print(sum(p.numel() for p in m.parameters())/1e6, 'M parameters')

# create a PyTorch optimizer
optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)
train()