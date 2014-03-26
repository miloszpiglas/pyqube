# pyqube.py

import collections

from views import View, Condition, Aggregate        

Alias = collections.namedtuple('Alias', ['view', 'alias'])
            
        
class Node(object):
    '''
        Tree's node. Represents single view. Each node might have
        parent and children. 
    '''
    
    def __init__(self, aliasView, relation=None):
        '''
            Initialise node. 
            params:
                - aliasView: pair of view and its alias (see: named tuple Alias)
                - relation: defines relation of this view to its parent
        '''
        self.av = aliasView
        self.children = []
        self.relation = relation
        
    def addJoin(self, aliasView, relation):
        '''
            Adds join to this node. 
        '''
        nn = Node(aliasView, relation)
        self.children.append(nn)
        return nn
    
    def toString(self, parentAlias=None):
        s = self.av.view.src+' '+self.av.alias
        if self.relation:
            s += ' on ' + self.relation.toString(parentAlias, self.av)
        for ch in self.children:
            s += '\n join ' + ch.toString(self.av)
        return s
            
class Tree(object):
    '''
        Defines order of joining views in single select query. Each
        node of tree represents single view used in query. All children
        of node are views, which are directly joined with node.
    '''
    
    def __init__(self, schema):
        self.root = None
        self.viewNode = {}
        self.idx = 0
        self.schema = schema
    
    def addJoin(self, view):
        '''
            Add view to join. If it is first view added to tree, it becomes
            root node. If tree has already root, proper view is find for passed one
            and join is created. 
            If passed view has no related views in tree, exception is raised.
        '''
        if not self.root:
            self.root = Node(Alias(view, 'a'+str(self.idx)))
            self.viewNode[view] = self.root
        elif not self.viewNode.has_key(view):
            related = self.schema.relatedViews(view)
            for v in related:
                if self.viewNode.has_key(v):
                    relation = self.schema.relation(v, view)
                    nn = self.viewNode[v].addJoin(Alias(view, 'a'+str(self.idx)), relation)
                    self.viewNode[view] = nn
                    break
            else:
                raise Exception('No related view in tree')
        self.idx += 1
        
    def createString(self):
        '''
            Uses tree to create full 'FROM' clause.
        '''
        return self.root.toString()
        
    def getAlias(self, view):
        '''
            Finds alias for view.
        '''
        return self.viewNode[view].av.alias
        
        
def equal(value=None):
    return Condition('= %s', value)        

def greater(value=None):
    return Condition('> %s', value)
    
def lesser(value=None):
    return Condition('< %s', value)

def incond(value=[]):
    return Condition(' in ( %s )', ','.join(value))

def avg(attr):
    return Aggregate('AVG', attr)
    
def aggrSum(attr):
    return Aggreget('SUM', attr)
    
def aggrCount(attr):
    return Aggregate('COUNT', attr)
        
class QueryBuilder(object):
    '''
        Uses selected view attributes to build SELECT query.
    '''
    
    def __init__(self, schema):
        self.attrs = []
        self.tree = Tree(schema)
        
    def select(self, selectAttr):
        '''
            Add attribute to selected list. Also prepares
            JOINs between views.
        '''
        self.tree.addJoin(selectAttr.view)
        self.attrs.append(selectAttr)
        
    def _validate(self):
        groupSet = frozenset([ a for a in self.attrs if a.groupBy and a.visible])
        aggrSet = frozenset([ a for a in self.attrs if a.aggregate and a.visible])
        visibleSet = frozenset([a for a in self.attrs if a.visible])
        if (groupSet or aggrSet) and not (aggrSet.isdisjoint(groupSet) and visibleSet == (groupSet | aggrSet)):
            print visibleSet
            print groupSet
            print aggrSet
            raise Exception('aggregate and group by') 
        
    def _joins(self):
        self._validate()
        query = 'select '
        attrList = []
        orderList = []
        groupList = []
        whereList = []
        for a in self.attrs:        
            alias = self.tree.getAlias(a.view)
            an = a.toString(alias)
            if a.visible:
                attrList.append(an)
            if a.orderBy:
                orderList.append(an)
            if a.groupBy:
                groupList.append(an)
            if a.condition:
                whereList.append(an+' '+str(a.condition))
        query += ', '.join(attrList)
        query += '\n from '+self.tree.createString()
        if whereList:
            query += '\n where '+ ' and '.join(whereList)
        if groupList:
            query += '\n group by '+ ', '.join(groupList)
        if orderList:
            query += '\n order by '+ ', '.join(orderList)
        return query
        
    def build(self):
        '''
            Builds query string
        '''
        return self._joins()
        
    def createView(self, name):
        '''
            Creates new view representing query, which might be used
            in next queries.
        '''
        query = self.build()
        return View('('+query+')', name, [a.realName() for a in self.attrs if a.visible])
