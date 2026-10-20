"""Text-free graph baseline: 2-layer GCN on each citation graph, 5 seeds.

Writes results/gcn.json with per-seed test accuracy on the exact S2019 / S2023 nodes,
plus per-node correctness (majority over seeds is not used; each seed is kept).
"""
import json

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F

SEEDS = [0, 1, 2, 3, 4]
torch.set_num_threads(8)
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def norm_adj(edge_index, n):
    ei = torch.cat([edge_index, edge_index.flip(0), torch.arange(n).repeat(2, 1)], 1)
    ei = torch.unique(ei, dim=1)
    deg = torch.zeros(n).scatter_add_(0, ei[0], torch.ones(ei.size(1)))
    w = deg[ei[0]].pow(-0.5) * deg[ei[1]].pow(-0.5)
    # CSR: same matrix, ~3x faster sparse matmul on CPU than COO
    return torch.sparse_coo_tensor(ei, w, (n, n)).coalesce().to_sparse_csr()


class GCN(torch.nn.Module):
    def __init__(self, d_in, d_hid, d_out, p=0.5):
        super().__init__()
        self.l1, self.l2, self.p = torch.nn.Linear(d_in, d_hid), torch.nn.Linear(d_hid, d_out), p
        self.bn = torch.nn.BatchNorm1d(d_hid)

    def forward(self, x, a):
        h = torch.sparse.mm(a, self.l1(x))
        h = F.dropout(F.relu(self.bn(h)), self.p, self.training)
        return torch.sparse.mm(a, self.l2(h))


def train(x, a, y, tr, va, test_nodes, seed, epochs=300):
    torch.manual_seed(seed); np.random.seed(seed)
    m = GCN(x.size(1), 256, int(y.max()) + 1).to(DEV)
    opt = torch.optim.Adam(m.parameters(), lr=0.01, weight_decay=5e-4)
    best, best_pred = -1, None
    for ep in range(epochs):
        m.train(); opt.zero_grad()
        F.cross_entropy(m(x, a)[tr], y[tr]).backward(); opt.step()
        if ep % 5 == 4:
            m.eval()
            with torch.no_grad():
                pred = m(x, a).argmax(1)
            v = (pred[va] == y[va]).float().mean().item()
            if v > best:
                best, best_pred = v, pred.clone()
        if ep % 50 == 49:
            print(f"    epoch {ep + 1}/{epochs}  best val {best:.3f}", flush=True)
    correct = (best_pred[test_nodes] == y[test_nodes]).int().cpu()
    return best, correct


def ogbn():
    base = "data/ogbn/arxiv"
    x = torch.from_numpy(pd.read_csv(f"{base}/raw/node-feat.csv.gz", header=None, dtype=np.float32).values)
    y = torch.tensor(pd.read_csv(f"{base}/raw/node-label.csv.gz", header=None)[0].values)
    year = pd.read_csv(f"{base}/raw/node_year.csv.gz", header=None)[0].values
    e = torch.tensor(pd.read_csv(f"{base}/raw/edge.csv.gz", header=None).values.T)
    pid = pd.read_csv(f"{base}/mapping/nodeidx2paperid.csv.gz")["paper id"].astype(str).tolist()
    tr = torch.tensor(np.where(year <= 2017)[0]); va = torch.tensor(np.where(year == 2018)[0])
    ids = [json.loads(l)["id"] for l in open("data/S2019.jsonl", encoding="utf-8")]
    pos = {p: i for i, p in enumerate(pid)}
    return x, norm_adj(e, x.size(0)), y, tr, va, torch.tensor([pos[i] for i in ids]), ids


def arxiv2023():
    base = "data/arxiv2023"
    x = torch.load(f"{base}/processed/features.pt").float()
    y = torch.load(f"{base}/processed/labels.pt").long().view(-1)
    e = torch.load(f"{base}/processed/edge_index.pt").long()
    rd = lambda f: pd.read_csv(f"{base}/split/{f}.csv.gz").iloc[:, 0].values
    ids = pd.read_csv(f"{base}/raw/ids.csv.gz")["ids"].astype(str).tolist()
    test = rd("test")
    return (x, norm_adj(e, x.size(0)), y, torch.tensor(rd("train")), torch.tensor(rd("valid")),
            torch.tensor(test), [ids[i] for i in test])


def main():
    out = {}
    print("device:", DEV, torch.cuda.get_device_name(0) if DEV.type == "cuda" else "", flush=True)
    for name, loader in [("S2019", ogbn), ("S2023", arxiv2023)]:
        x, a, y, tr, va, te, ids = loader()
        x, a, y, tr, va, te = (t.to(DEV) for t in (x, a, y, tr, va, te))
        print(name, "nodes", x.size(0), "feat", x.size(1), "classes", int(y.max()) + 1,
              "train/val/test", len(tr), len(va), len(te), flush=True)
        runs = []
        for s in SEEDS:
            v, c = train(x, a, y, tr, va, te, s)
            runs.append({"seed": s, "val_acc": v, "test_acc": c.float().mean().item(), "correct": c.tolist()})
            print(f"  seed {s}: val {v:.3f} test {runs[-1]['test_acc']:.3f}", flush=True)
        out[name] = {"ids": ids, "runs": runs}
    json.dump(out, open("results/gcn.json", "w"))


if __name__ == "__main__":
    main()
