# pyqube.py

import collections

from views import *   

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
        s = self.av.view.source+' '+self.av.alias
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
    
def avg(attr):
    return Aggregate('AVG', attr)
    
def aggrSum(attr):
    return Aggreget('SUM', attr)
    
def aggrCount(attr):
    return Aggregate('COUNT', attr)
    
   
class QueryView(IView):

    def __init__(self, name, attrs, tree):
        IView.__init__(self, name)
        self.tree = tree
        self.attrs = attrs
        
    def _build(self, addWhere=True):
        query = 'SELECT '
        attrList = []
        orderList = []
        groupList = []
        whereList = []
        cc = 0
        for a in self.attrs:        
            alias = self.tree.getAlias(a.view)
            an = a.toString(alias)
            if a.visible:
                attrList.append(an)
            if a.orderBy:
                orderList.append(an)
            if a.groupBy:
                groupList.append(an)
            if a.condition and addWhere:
                cstr = a.condition.toString(an, cc)
                whereList.append(cstr[0])
                cc = cstr[1]
        query += ', '.join(attrList)
        query += '\n FROM '+self.tree.createString()
        if whereList:
            query += '\n WHERE '+ ' '.join(whereList)
        if groupList:
            query += '\n GROUP BY '+ ', '.join(groupList)
        if orderList:
            query += '\n ORDER BY '+ ', '.join(orderList)
        return query         
    
    @property    
    def source(self):
        vs = '('+self._build(False)+')'
        return vs
        
    def prepare(self):
        vs = self._build(True)
        params = {}
        cc = 0
        for a in self.attrs:
            if a.condition:
                names = a.condition.paramNames(cc)
                for n in names[0]:
                    params[n] = a
                cc = names[1]
        return (vs, params)
        
    def attribute(self, name):
        for a in self.attrs:
            if a.visible and a.realName() == name:
                return ViewAttr(a.realName(), self)
        else:
            raise Exception('Attribute '+name+' not found')
        
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
            
    def build(self):
        '''
            Builds query string
        '''
        return self.createQuery().prepare()
        
    def createQuery(self, name='Query'):
        self._validate()
        return QueryView(name, self.attrs, self.tree)
