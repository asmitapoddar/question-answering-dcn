import torch as th
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
import torch.optim as optim
import time

from model import *

th.manual_seed(1)

# Config flags.
TEST_DCN_MODEL_WITH_CPU = False

# Defaults/constants.
BATCH_SIZE = 64
DROPOUT = 0.3
HIDDEN_DIM = 200  # Denoted by 'l' in the paper.
MAX_ITER = 4
MAXOUT_POOL_SIZE = 16

# start test functions with test_
def test_example():
    pass

def test_dcn_model():
    # https://discuss.pytorch.org/t/solved-make-sure-that-pytorch-using-gpu-to-compute/4870/2
    # Is GPU available:
    print ("cuda device count = %d" % th.cuda.device_count())
    print ("cuda is available = %d" % th.cuda.is_available())
    device = th.device("cuda:0" if th.cuda.is_available() and (not TEST_DCN_MODEL_WITH_CPU) else "cpu")

    doc = th.randn(BATCH_SIZE, 30, HIDDEN_DIM, device=device) # Fake word vec dimension set to HIDDEN_DIM.
    que = th.randn(BATCH_SIZE, 5, HIDDEN_DIM, device=device)  # Fake word vec dimension set to HIDDEN_DIM.

    # Fake ground truth data (one batch of starts and ends):
    true_s = th.randint(0, doc.size()[1], (BATCH_SIZE,), device=device)
    true_e = th.randint(0, doc.size()[1], (BATCH_SIZE,), device=device)
    for i in range(BATCH_SIZE):
      true_s[i], true_e[i] = min(true_s[i], true_e[i]), max(true_s[i], true_e[i])

    # Run model.
    model = DCNModel(doc, que, BATCH_SIZE, device).to(device)
    loss, s, e = model.forward(doc, que, true_s, true_e)
    print("Predicted start: %s \nPredicted end: %s \nloss: %s" % (str(s), str(e), str(loss)))
    model.zero_grad()
    loss.backward()

    print("%d/%d parameters have non-None gradients." % (len([param for param in model.parameters() if param.grad is not None]), len(list(model.parameters()))))

def test_hmn():
    device = th.device("cuda:0" if th.cuda.is_available() else "cpu")
    hmn = HighwayMaxoutNetwork(BATCH_SIZE, DROPOUT, HIDDEN_DIM, MAXOUT_POOL_SIZE, device).to(device)
    u_t = th.ones(BATCH_SIZE, 2 * HIDDEN_DIM, 1, device=device)
    h_i = th.ones(BATCH_SIZE, HIDDEN_DIM, 1, device=device)
    u_si_m_1, u_ei_m_1 = th.ones(BATCH_SIZE, 2 * HIDDEN_DIM, 1, device=device), th.ones(BATCH_SIZE, 2 * HIDDEN_DIM, 1, device=device) #TODO device
    output = hmn.forward(u_t, h_i, u_si_m_1, u_ei_m_1)

    # Call backward on a scalar ("output" is of dimension BATCH_SIZE x 1)
    assert(output.size()[0] == hmn.batch_size)
    assert(output.size()[1] == 1)
    th.mean(output).backward()
    print("%d/%d parameters have non-None gradients." % (len([param for param in hmn.parameters() if param.grad is not None]), len(list(hmn.parameters()))))

def test_decoder():
    max_iter = 10
    device = th.device("cuda:0" if th.cuda.is_available() else "cpu")
    dpd = DynamicPointerDecoder(BATCH_SIZE, max_iter, DROPOUT, DROPOUT, HIDDEN_DIM, device).to(device)
    U = th.ones(BATCH_SIZE, 2 * HIDDEN_DIM, 50, device=device)
    alphas, betas, s, e = dpd.forward(U)
    loss = th.mean(th.mean(alphas, dim=0)) + th.mean(th.mean(betas, dim=0))
    dpd.zero_grad()
    loss.backward()
    print(loss)