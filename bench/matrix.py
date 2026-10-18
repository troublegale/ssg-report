# критерий: (вес, MkDocs, Sphinx, Pelican, Quarto), оценки 0..3
C = {
 "A1": (4, 1,3,1,3), "A2": (8, 2,3,1,3), "A3": (5, 1,3,0,3), "A4": (4, 1,3,0,3),
 "A5": (3, 1,2,1,3), "A6": (6, 1,3,0,3), "A7": (6, 1,2,1,3), "A8": (4, 2,3,1,2),
 "B1": (5, 3,2,1,3), "B2": (5, 3,3,2,2), "B3": (5, 1,3,0,3),
 "C1": (6, 3,2,0,0), "C2": (6, 2,3,1,1), "C3": (3, 2,3,2,1), "C4": (3, 2,3,0,2),
 "C5": (5, 3,3,2,2), "C6": (6, 3,2,3,1), "C7": (8, 1,3,2,2), "C8": (8, 3,2,2,2),
}
names = ["MkDocs", "Sphinx", "Pelican", "Quarto"]
assert sum(v[0] for v in C.values()) == 100
def score(keys, j): 
    w = sum(C[k][0] for k in keys); return sum(C[k][0]*C[k][j+1] for k in keys)/(3*w)*100
groups = {"A": [k for k in C if k[0]=="A"], "B": [k for k in C if k[0]=="B"], "C": [k for k in C if k[0]=="C"], "ALL": list(C)}
for g, ks in groups.items():
    print(g, [f"{n}={score(ks,j):.1f}" for j,n in enumerate(names)])
# сценарий «научная статья»: веса A ×2
import copy
for label, mult in [("science A*2", {"A":2,"B":1,"C":1}), ("ops C*2", {"A":1,"B":1,"C":2})]:
    tot=[0]*4; W=0
    for k,v in C.items():
        w=v[0]*mult[k[0]]; W+=w
        for j in range(4): tot[j]+=w*v[j+1]
    print(label, [f"{n}={t/(3*W)*100:.1f}" for n,t in zip(names,tot)])
# сценарий «сайт-отчёт без исполняемого контента и библиографии»: A6,A7 исключены, A — ×0.5, C6,C8 — ×2
tot=[0]*4; W=0
for k,v in C.items():
    m = 0 if k in ("A6","A7") else (0.5 if k[0]=="A" else (2 if k in ("C6","C8") else 1))
    w=v[0]*m; W+=w
    for j in range(4): tot[j]+=w*v[j+1]
print("report-site", [f"{n}={t/(3*W)*100:.1f}" for n,t in zip(names,tot)])
