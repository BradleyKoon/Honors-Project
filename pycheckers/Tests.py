import networkx as nx 

class Node(object):
    def __init__(self, id, parent):
        self.id = id 
        self.parent = parent 

def crossover(c1, c2):
    T = nx.Graph() 
    T.add_node("root") 
    for i in range(len(c1)):
        if c1[i] == c2[i]:
            if i == 0:
                T.add_node(c1[i]) 
                T.add_edge("root", c1[i]) 
            else:
                T.add_node(c1[i]) 
                T.add_edge(c1[i-1], c1[i]) 
        else:
            T.add_node(c1[i]) 
            T.add_edge(c1[i-1], c1[i]) 
            T.add_node(c2[i]) 
            T.add_edge(c2[i-1], c2[i]) 
    return T 

c1 = [1,2,3,4]
c2 = [1,2,3,5] 

T = crossover(c1, c2) 

def foo():
    for i in range(0,5):
        print("hello world")
    print(i) 

foo() 