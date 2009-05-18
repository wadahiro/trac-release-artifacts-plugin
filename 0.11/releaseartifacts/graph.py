# -*- coding: utf-8 -*-

from trac.core import *
from trac.resource import ResourceNotFound
from trac.ticket.model import Milestone
from trac.versioncontrol import Changeset
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol import Changeset, Node
from releaseartifacts.versioncontrol import SCMTag, SCMBranch
import re

class GraphManager(object):
    
    def __init__(self, env):
        self.env = env
        
    def _to_flat_nodes(self, nodes, collect):
        for n in nodes:
            collect.append(n)
            self._to_flat_nodes(n.get_nexts(), collect)
        return collect
        
    def to_graphviz(self, nodes, milestones):
        
        flat_nodes = []
        self._to_flat_nodes(nodes, flat_nodes)
        
        g = Graph(self.env)
        for index, milestone in enumerate(milestones):
            sg = SubGraph(self.env, index, milestone)
            
            for a in milestone.artifacts:
                for n in flat_nodes:
                    if a.tag == n.path:
                        sg.add_node(n)
                        
            g.add_subgraph(sg)
            
        g.add_depends(nodes)
            
        return g.get_graph()
    
    def to_graphnode(self, roots):
        rtn = []
        for node in roots:
            graph_node = RootGraphNode(self.env, node)
            self._to_graphnode(graph_node, node)
            rtn.append(graph_node)
        return rtn
    
    def _to_graphnode(self, graph_node, node):
        for next in node.get_next_nodes():
            sub = self._to_tag_or_branch(next)
            graph_node.append(sub)
            self._to_graphnode(sub, next)
            
    def _to_tag_or_branch(self, node):
        if isinstance(node, SCMBranch):
            return BranchGraphNode(self.env, node)
        if isinstance(node, SCMTag):
            return TagGraphNode(self.env, node)
        
    def to_s(self, nodes):
        for t in nodes:
            self.env.log.info('ROOT: %s' % t.label)
            if len(t.get_nexts()) > 0:
                for next in t.get_nexts():
                    self.node_to_s(next, '  ')
                        
    def node_to_s(self, node, indent):
        self.env.log.info('%s--> %s, %s' % (indent, node.label, node.type))
        if len(node.get_nexts()) > 0:
            for next in node.get_nexts():
                indents = indent + '  '
                self.node_to_s(next, indents)

class GraphNode(object):
    
    def __init__(self, env, scm_node):
        self.env = env
        self.path = scm_node.path
        self.rev = scm_node.rev
        self.label = scm_node.label
        self.id = scm_node.label
        self.nexts = []
        self.parent = None
        self.type = scm_node.get_type()
            
    def get_type(self):
        return self.type
        
    def get_nexts(self):
        return self.nexts
        
    def append(self, node):
        self.nexts.append(node)
        return node
    
    def set_parent(self, node):
        self.parent = node
    
    def __eq__(self, other):
        if not isinstance(other, GraphNode):
            return False
        return self.name == other.name
    
    def get_graph(self):
        return '"%s" [label="%s", shape="box"];\n' % (self.id, self.label)
    
class RootGraphNode(GraphNode):
    
    def __init__(self, env, scm_node):
        GraphNode.__init__(self, env, scm_node)
        self.type = 'Root'
        
    def get_graph(self):
        return '"%s" [label="ROOT: %s", shape="box"];\n' % (self.id, self.label)

class BranchGraphNode(GraphNode):
    
    def __init__(self, env, scm_node):
        GraphNode.__init__(self, env, scm_node)
        
    def get_graph(self):
        return '"%s" [label="<<BRANCH>>\\n\\n%s", fontsize="12", \
shape="box"];\n' % (self.id, _layout_graphviz_label(self.label, 10))

class TagGraphNode(GraphNode):
    
    def __init__(self, env, scm_node):
        GraphNode.__init__(self, env, scm_node)
        self.counter = 0
        
    def get_fontcolor(self):
        return 'black'
        
    def get_color(self):
        return '#336666'

    def get_fillcolor(self):
        return '#99FFCC'
    
    def get_graph(self):
        if self.counter == 0:
            id = self.id
            style = 'filled, rounded'
            ext =''
            fontcolor = self.get_fontcolor()
        else:
            id = '%s_%i' % (self.id, self.counter)
            style = 'dashed, rounded'
            ext =  '"%s" -> "%s" [style="dashed", dir="none"];\n' % (self.id, id)
            fontcolor = '#336666'
            
        self.counter += 1
        return '"%s" [label="<<TAG>>\\n\\n%s", shape="box", style="%s", \
fontsize="10", fontcolor="%s", color="%s", \
fillcolor="%s"];\n  %s' % (id, _layout_graphviz_label(self.label, 10), style,
                                         fontcolor, self.get_color(), self.get_fillcolor(),
                                         ext)

class Graph(object):
    
    def __init__(self, env):
        self.env = env
        self.subgraphs = []
    
    def add_subgraph(self, subgraph):
        self.subgraphs.append(subgraph)
        
    def add_depends(self, nodes):
        self.nodes = nodes
        
    def get_graph(self):
        graph = """
    {{{
#!graphviz
digraph release_artifact {
"""
        #Write Rank
        graph += '"invis_root" [style=invis, width=0, label=""];\n'
        graph += ''.join('"invis_milestone_%i" [style=invis, width=0, label=""];\n' % i for i in range(len(self.subgraphs)))
        graph += '"invis_root" -> '
        graph += '->'.join('"invis_milestone_%i"' % i for i in range(len(self.subgraphs)))
        graph += ' [shape="point", width="0", style="invis"]\n'

        for subgraph in self.subgraphs:
            graph += subgraph.get_graph()
            
        #Write root, branch
        for n in self.nodes:
            graph = self._to_node_graph(graph, n)
        
        #Write dependencies
        for n in self.nodes:
            graph = self._to_dependencies_graph(graph, n)
            graph += '\n'

        graph += '\n  }\n'
        return graph
    
    def _to_node_graph(self, graph, node):
        
        if node.type == 'Root' or node.type == 'Branch':
            graph += node.get_graph()
            
        for n in node.get_nexts():
            graph = self._to_node_graph(graph, n)
        return graph
    
    def _to_dependencies_graph(self, graph, node):
            
        for n in node.get_nexts():
            graph += '"%s" -> "%s"\n' % (node.id, n.id)
            graph = self._to_dependencies_graph(graph, n)
        return graph
      
class SubGraph(object):
    
    def __init__(self, env, index, milestone):
        self.env = env
        self.milestone = milestone
        self.nodes = []
        self.id = 'milestone_%i' % index

    def get_label(self):
        return self.milestone.name
    
    def add_node(self, node):
        self.nodes.append(node)

    def get_graph(self):
        graph = """
  subgraph cluster_%s {
    label="%s";
    fontsize="15";
    style="filled";
    fillcolor="gray";
    URL="milestone:'%s'";
    "%s" [shape="point", width="0", style="invis"];
    {rank=same; "%s"; "invis_%s"}
""" % (self.id, self.get_label(), self.milestone.name, self.id, self.id, self.id)
        
        for node in self.nodes:
            graph += node.get_graph()

        graph += '\n  }\n'
        
        return graph
    
def _layout_graphviz_label(label, max_chars_of_line):
    
    str_list = []
    begin = 0
    for i in range(len(label)):
        if (i + 1) % max_chars_of_line == 0:
            str_list.append(label[begin:(i + 1)])
            begin = i + 1
            
    if (len(label) % max_chars_of_line) > 0:
	    str_list.append(label[-(len(label) % max_chars_of_line):])
    
    return '\\n'.join(str_list)
    
