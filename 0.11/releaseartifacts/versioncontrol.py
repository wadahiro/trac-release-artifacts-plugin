# -*- coding: utf-8 -*-

from trac.core import *
from trac.env import IEnvironmentSetupParticipant
from trac.resource import ResourceNotFound
from trac.ticket.model import Milestone
from trac.versioncontrol import Changeset
from trac.versioncontrol.web_ui.util import *
from trac.versioncontrol import Changeset, Node
import re

class SCMNode(object):

    def __init__(self, env, path):
        self.env = env
        self.path = path[0]
        self.rev = path[1]
        self.id = _normalize_id('%s_at_%s' % (path[0], path[1]))
        self.next_nodes = []
        self.label = '%s@%s' % (self.path, self.rev)
        self.parent = None
        
    def __str__(self):
        return '%s@%s, %s' % (self.path, self.rev, self.get_type())
        
    def __eq__(self, other):
        if not isinstance(other, SCMNode):
            return False
        return self.path == other.path and self.rev == other.rev and self.get_type() == other.get_type()
    
    def __cmp__(self, other):
        if other == None:
            return -1
        if self.path != other.path:
            return cmp(self.path, other.path)
        return cmp(int(self.rev), int(other.rev))
    
    def add_next(self, scm_node):
        if not scm_node in self.next_nodes:
            self.next_nodes.append(scm_node)
            
    def remove_next(self, scm_node):
        self.next_nodes.remove(scm_node)
        
    def replace(self, old_node, new_node):
        index = self.next_nodes.index(old_node)
        self.next_nodes[index] = new_node
        new_node.set_parent(self)
            
    def set_parent(self, scm_node):
        self.parent = scm_node
        
    def get_parent(self):
        return self.parent
        
    def get_next_nodes(self):
        return self.next_nodes
        
    def get_type(self):
        return 'Node'
    
    def sort(self):
        self.next_nodes.sort()
        for n in self.next_nodes:
            n.sort()
    
class SCMBranch(SCMNode):
        
    def __init__(self, env, path):
        SCMNode.__init__(self, env, path)
 
    def get_type(self):
        return 'Branch'
        
class SCMTag(SCMNode):
        
    def __init__(self, env, path, milestone=None):
        SCMNode.__init__(self, env, path)

    def set_parent(self, scm_node):
        self.parent = scm_node
        self.base = scm_node
        
    def get_base(self):
        return self.base
        
    def get_type(self):
        return 'Tag'
    
    def clear_next(self):
        self.next_nodes = []
               
class CopiedFrom(SCMNode):
        
    def get_type(self):
        return 'CopiedFrom'
               
class SCMManager:
    
    def __init__(self, env, req):
        self.env = env
        self.req = req
        self.authname = req.authname
        self.repos = env.get_repository(req.authname)
        self.youngest_rev = self.repos.youngest_rev
        
    def artifacts_to_nodes(self, artifacts):
        nodes = []
        for artifact in artifacts:
            try:
                self.parse(nodes, artifact.milestone, artifact.scm_path, self.youngest_rev)
            except ResourceNotFound:
                pass
            
        roots = [n for n in nodes if n.rev == 0]
        for n in roots:
            n.sort()
            
        self.env.log.info('sorted')
        
        self.to_s(nodes)
        
        for n in roots:
            self._resolve_node_relation(n)
            
        self.env.log.info('resolved relation')
        
        self.to_s(nodes)
        
        for n in roots:
            self._remove_unused_node(n)
            
        self.env.log.info('remove unused node')
        
        self.to_s(nodes)
        
        for n in roots:
            self._resolve_node_relation(n)
            
        self.env.log.info('resolved relation 2')
        
        self.to_s(nodes)

        return nodes
    
    def _remove_unused_node(self, current):
        parent = current.get_parent()
        if parent and current.get_next_nodes():
            if current.get_type() == 'CopiedFrom':
                parent.remove_next(current)
                for new_child in current.get_next_nodes():
                    parent.add_next(new_child)
                    new_child.set_parent(parent)

        for child in current.get_next_nodes():
            self._remove_unused_node(child)

    def _resolve_node_relation(self, node):
        before = None
        for n in reversed(node.get_next_nodes()):
            self._resolve_node_relation(n)
            
            if before:
               self._change_node_relation(before, n)
            before = n
                
    def _change_node_relation(self, node_a, node_b):
        if node_a.path == node_b.path:
            self._do_relation_by_revision(node_a, node_b)
            
        elif isinstance(node_a, SCMTag) and isinstance(node_b, SCMTag):
            if node_a.get_base().path == node_b.get_base().path:
                self._do_relation_by_revision(node_a, node_b)
                
    def _do_relation_by_revision(self, node_a, node_b):
        if int(node_a.rev) < int(node_b.rev):
            node_a.add_next(node_b)
            p = node_b.get_parent()
            if p:
                p.remove_next(node_b)
            node_b.set_parent(node_a)
        elif int(node_a.rev) > int(node_b.rev):
            node_b.add_next(node_a)
            p = node_a.get_parent()
            if p:
                p.remove_next(node_a)
            node_a.set_parent(node_b)
            
    def new_tag(self, nodes, path, rev, milestone):
        tag = SCMTag(self.env, (path, rev), milestone)
            
        #If the tag is cached in nodes, get from nodes.
        return _list_cache(nodes, tag)

    def new_copied_from(self, nodes, path, rev):
        copied_from = CopiedFrom(self.env, (path, rev))
        
        #If the copiedfrom is cached in nodes, get from nodes.
        return _list_cache(nodes, copied_from)

    def new_branch(self, nodes, path, rev):
        branch = SCMBranch(self.env, (path, rev))
        
        if branch in nodes:
            return (nodes[nodes.index(branch)], True)
        else:
            nodes.append(branch)
            return (branch, False)
    
    def parse(self, nodes, milestone, path, start_rev):
        
        #Get latest revision of Tag.
        rev = self.get_latest_rev(path)
        
        current_child = None
        
        while int(rev) > 0:
            
            if not current_child:
                #Create Tag at first time in this loop.
                node = self.new_tag(nodes, path, rev, milestone)
            else:
                node = self.new_copied_from(nodes, path, rev)
            
            if current_child:
                node.add_next(current_child)
                current_child.set_parent(node)
                
            copied_rev, base_path, base_rev = self.get_copied_from(node.path,
                                                                   node.rev)
            if rev == copied_rev:
                current_child = node
            else:
                # TODO: don't write hard code
                if re.search('branches', path):
                    parent_node, end = self.new_branch(nodes, path, copied_rev)
                elif re.search('tags', path):
                    parent_node = self.new_tag(nodes, path, copied_rev, milestone)
                    end = False
                else:
                    parent_node = self.new_copied_from(nodes, path, copied_rev)
                    end = False
            
                parent_node.add_next(node)
                node.set_parent(parent_node)
            
                if end:
                    break
            
                current_child = parent_node
            
            #setting next parse path and rev.
            path = base_path
            rev = str(int(copied_rev) - 1)

    def get_latest_rev(self, path):
        history = get_existing_node(self.env, self.repos, path, self.youngest_rev).get_history
        for old_path, old_rev, old_chg in history(1):
            return old_rev

    def get_copied_from(self, path, rev, limit=200):
        if path.startswith('trunk/'):
            return (0, None, None)
            
        history = get_existing_node(self.env, self.repos, path, rev).get_history
        for old_path, old_rev, old_chg in history(limit):
            changeset = self.repos.get_changeset(old_rev)
            changes = changeset.get_changes()
            
            for path, kind, change, base_path, base_rev in changes:
                if kind == 'dir' and change == 'copy':
                    self.env.log.debug("Directory Copy: old_rev=%s, base_path=%s, base_rev=%s" %(old_rev, base_path, base_rev))
                    return (old_rev, base_path, base_rev)
        return (0, None, None)
    
    def get_roots(self, nodes):
        return [node for node in nodes if str(node.rev) == '0']
    
    def to_s(self, nodes):
        #debug code
        for t in nodes:
            if str(t.rev) == '0':
                self.env.log.info('ROOT: %s@0' % t.path)
                if len(t.get_next_nodes()) > 0:
                    for next in t.get_next_nodes():
                        self.node_to_s(next, '  ')
                        
    def node_to_s(self, node, indent):
        self.env.log.info('%s--> %s@%s, %s' % (indent, node.path, str(node.rev), node.get_type()))
        if len(node.get_next_nodes()) > 0:
            for next in node.get_next_nodes():
                indents = indent + '  '
                self.node_to_s(next, indents)
    
def _normalize_id(id):
    id = re.sub('@', '__at__', id)
    return re.sub('\.|/|-', '_', id)

def _is_tag(path):
    return path.startswith('tags/')

def _is_branch(path):
    return path.startswith('branches/')

def _list_cache(list, obj):
    if obj in list:
        obj = list[list.index(obj)]
    else:
        list.append(obj)
    return obj

def _rev_plus(rev, number):
    return str(int(rev) + number)