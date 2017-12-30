from utils import Doc
import torch
from torch.autograd import Variable
from models.seq2seq.data import SimplePairGenerator as PairGenerator
from models.seq2seq.masked_cross_entropy import masked_cross_entropy
from models.seq2seq.model import EncoderRNN, LuongAttnDecoderRNN
from models.seq2seq.config import USE_CUDA

pg = PairGenerator()

random_batch = pg.random_batch
pg.trim(2, 10)
pg.separate()
small_batch_size = 3
input_batches, input_lengths, target_batches, target_lengths = random_batch(small_batch_size,'test')

print('input_batches', input_batches.size()) # (max_len x batch_size)
print('target_batches', target_batches.size()) # (max_len x batch_size)

small_hidden_size = 8
small_n_layers = 2

encoder_test = EncoderRNN(len(Doc.get_vocab()), small_hidden_size, small_n_layers)
decoder_test = LuongAttnDecoderRNN('general', small_hidden_size, len(Doc.get_vocab()), small_n_layers)

if USE_CUDA:
    encoder_test.cuda()
    decoder_test.cuda()

encoder_outputs, encoder_hidden = encoder_test(input_batches, input_lengths, None)

print('encoder_outputs', encoder_outputs.size()) # max_len x batch_size x hidden_size
print('encoder_hidden', encoder_hidden.size()) # n_layers * 2 x batch_size x hidden_size
max_target_length = max(target_lengths)

# Prepare decoder input and outputs
decoder_input = Variable(torch.LongTensor([Doc.get_vocab()['<SOS>']] * small_batch_size))
decoder_hidden = encoder_hidden[:decoder_test.n_layers] # Use last (forward) hidden state from encoder
all_decoder_outputs = Variable(torch.zeros(max_target_length, small_batch_size, decoder_test.output_size))

if USE_CUDA:
    all_decoder_outputs = all_decoder_outputs.cuda()
    decoder_input = decoder_input.cuda()

# Run through decoder one time step at a time
for t in range(max_target_length):
    decoder_output, decoder_hidden, decoder_attn = decoder_test(
        decoder_input, decoder_hidden, encoder_outputs
    )
    all_decoder_outputs[t] = decoder_output # Store this step's outputs
    decoder_input = target_batches[t] # Next input is current target

# Test masked cross entropy loss
loss = masked_cross_entropy(
    all_decoder_outputs.transpose(0, 1).contiguous(),
    target_batches.transpose(0, 1).contiguous(),
    target_lengths
)
print('loss', loss.data[0])
