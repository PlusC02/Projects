# Overview
The project consists of different building blocks of Transfomer model that are built manually and a generative model that is made of decoder only.

The model is trained in Colab with Free tier GPU, therefore, most hyperparameter I set is compromised.

## Purpose of the Project
The project aims to increase my understanding on Transfomer Architecture.

Despite learned in University, I have never coded a Transformer along with understanding the paper.

## Architecture
The transfomer here used only the decoder part of the original paper but all components in the original paper are used.

The following are:
### Embedding Layer
The input are first embedded so as to learn the high-dimensional information of the context. The embedding layer would be learned when training the model

### Positional Encoding
Since the model takes multiple inputs in parallel, we need to add information so as to provide the spatial information for the model to learn the contextual meaning.

### Decoder_block
As we need to repeat attention multiple times, we created a decoder_block to store the action we need to do. 

The decoder_block is the self attention as well as the feedforward neural network

## References
- [Attention Is All You Need](https://arxiv.org/abs/1706.03762) paper.
- [Let's build GPT: from scratch, in code, spelled out.](https://www.youtube.com/watch?v=kCc8FmEb1nY&t=5722s) video by Andrej Karpathy
