# pyqube.py

import collections
        
class Schema(object):

    def __init__(self):
        self.views = {} 
        self.rels = {}
        
    def addView(self, view, relation=None):
        if not relation:
            self.views[view] = []
        else:
            rv = relation.related(view).view
            if self.views.has_key(rv):
                self.views[view] = [rv]
                self.views[rv].append(view)
                self.rels[(view, rv)] = relation
                self.rels[(rv, view)] = relation
            else:
                raise Exception('no related views')
                
    def relatedViews(self, view):
        return self.views[view]
        
    def relation(self, view, related):
        if self.views.has_key((view, related)):
            return self.views[(view, related)]
        elif self.views.has_key((related, view)):
            return self.views[(related, view)]
        return None

Alias = collections.namedtuple('Alias', ['view', 'alias'])
        
class AttrPair(object):

    def __init__(self, leftAttr, rightAttr):
        self.left = leftAttr
        self.right = rightAttr
        
    def related(self, view):
        if self.left.view == view:
            return self.right
        elif self.right.view == view:
            return self.left
        else:
            return None
    
    def attribute(self, view):
        if view == self.left.view:
            return self.left
        elif view == self.right.view:
            return self.right
        else:
            raise Exception('Views do not match')
            
    def toString(self, vleft, vright):
        a = vleft.alias+'.'+self.attribute(vleft.view).name
        b = vright.alias+'.'+self.attribute(vright.view).name
        return a+' = '+b
            
            
class Relation(object):

    def __init__(self, pairs):
        self.pairs = pairs
        
    def related(self, view):
        return self.pairs[0].related(view)
        
    def toString(self, vleft, vright):
        return ' AND '.join([p.toString(vleft, vright) for p in self.pairs])
        
    def __str__(self):
        return '%s %s' %(self.pairs[0].left, self.pairs[0].right)
        
class Node(object):

    def __init__(self, aliasView, relation=None):
        self.av = aliasView
        self.children = []
        self.relation = relation
        
    def addJoin(self, aliasView, relation):
        nn = Node(aliasView, relation)
        self.children.append(nn)
        return nn
    
    def toString(self, parentAlias=None):
        s = self.av.view.src+' '+self.av.alias
        if self.relation:
            s += ' on ' + self.relation.toString(parentAlias, self.av)
        for ch in self.children:
            s += ' join ' + ch.toString(self.av)
        return s
            
class Tree(object):

    def __init__(self):
        self.root = None
        self.viewNode = {}
        self.idx = 0
        
    def addJoin(self, view, rel=None):
        if not self.root:
            self.root = Node(Alias(view, 'a'+str(self.idx)))
            self.viewNode[view] = self.root
        elif rel and not self.viewNode.has_key(view):
            rv = rel.related(view).view
            if self.viewNode.has_key(rv):
                nn = self.viewNode[rv].addJoin(Alias(view, 'a'+str(self.idx)), rel)
                self.viewNode[view] = nn
            else:
                raise Exception('No related view in tree')
        elif not self.viewNode.has_key(view):
            raise Exception('Undefined relation')
        self.idx+=1
        
    def createString(self):
        return self.root.toString()
        
    def getAlias(self, view):
        return self.viewNode[view].av.alias
        
class ViewAttr(object):

    def __init__(self, name, view):
        self.name = name
        self.view = view 
        
    def select(self, visible=True, orderBy=False, groupBy=False, condition=None, aggregate=None, altName=None):
        sa = SelectAttr(self.name, self.view)
        sa.visible = visible
        sa.orderBy = orderBy
        sa.groupBy = groupBy
        sa.condition = condition
        sa.aggregate = aggregate
        sa.altName = altName
        return sa
        
    def __str__(self):
        return '%s.%s'%(self.view.name, self.name)
    
    def _prepareStr(self, alias):
        return '%s.%s' % (alias, self.name)
            
    def toString(self, alias):
        return self._prepareStr(alias)
        
        
class SelectAttr(ViewAttr):

    def __init__(self, name, view):
        ViewAttr.__init__(self, name, view)
        self.visible = True
        self.orderBy = False
        self.groupBy = False
        self.condition = None
        self.aggregate=None
        self.altName = None
        
    def __str__(self):
        if self.aggregate:
            return str(self.aggregate(ViewAttr.__str__(self)))
        return ViewAttr.__str__(self)
        
    def __repr__(self):
        str(self)
    
    def _prepareStr(self, alias):
        base = ViewAttr._prepareStr(self, alias)
        if self.aggregate:
            base = str(self.aggregate(base))
        if self.altName:
            base += ' as '+self.altName
        return base
        
    def realName(self):
        if self.altName:
            return self.altName
        return self.name
        
class View(object):

    def __init__(self, src, name, attrNames):
        self.src = src
        self.attrs = {}
        for n in attrNames:
            self.attrs[n] = ViewAttr(n, self)
        self.name = name    
    
    def attribute(self, name):
        return self.attrs[name]
        
    def __str__(self):
        return self.src
        
    def __repr__(self):
        return self.src

class Condition(object):

    def __init__(self, fmt, value=None):
        self.fmt = fmt
        self.value = value
        
    def __str__(self):
        if self.value:
            return self.fmt % self.value
        else:
            return self.fmt % '?'
            
class Aggregate(object):

    def __init__(self, name, attr):
        self.name = name
        self.attr = attr
        
    def __str__(self):
        return '%s( %s )' % (self.name, self.attr)
        
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

    def __init__(self):
        self.attrs = []
        self.tree = Tree()
        
    def select(self, selectAttr, relation=None):
        self.tree.addJoin(selectAttr.view, relation)
        self.attrs.append(selectAttr)
        
    def _validate(self):
        groupSet = frozenset([ a for a in self.attrs if a.groupBy and a.visible])
        aggrSet = frozenset([ a for a in self.attrs if a.aggregate and a.visible])
        visibleSet = frozenset([a for a in self.attrs if a.visible])
        if not (aggrSet.isdisjoint(groupSet) and visibleSet == (groupSet | aggrSet)):
            print visibleSet
            print groupSet
            print aggrSet
            raise Exception('aggregate and group by') 
        
    def _joins2(self):
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
        query += ' from '+self.tree.createString()
        if whereList:
            query += ' where '+ ' and '.join(whereList)
        if groupList:
            query += ' group by '+ ', '.join(groupList)
        if orderList:
            query += ' order by '+ ', '.join(orderList)
        return query
        
    def build(self):
        return self._joins2()
        
    def createView(self, name):
        query = self.build()
        return View(query, name, [a.realName() for a in self.attrs if a.visible])


def main():
    vboo = View('books', 'Books', ['title', 'author', 'year', 'publisher', 'category'])
    vpub = View('publishers', 'Publishers', ['id', 'name', 'city'])
    catv = View('categories', 'Categories', ['id', 'category_name'])
    citv = View('cities', 'Cities', ['id', 'city_name'])
    
    schema = Schema()
    schema.addView(vboo)
    rbp = Relation([AttrPair(vboo.attribute('publisher'), vpub.attribute('id'))])
    schema.addView(vpub, rbp)
    
    rpc = Relation([AttrPair(vpub.attribute('city'), citv.attribute('id'))])
    schema.addView(citv, rpc)
    
    rbc = Relation([AttrPair(vboo.attribute('category'), catv.attribute('id'))])
    schema.addView(catv, rbc)
    
    builder = QueryBuilder()
    autAttr = vboo.attribute('author').select(aggregate=aggrCount, altName='Authors')
    builder.select(autAttr)
    
    yearAttr = vboo.attribute('year').select(condition=incond(['2012','2013']), orderBy=True, groupBy=True)
    builder.select(yearAttr)
    #titleAttr = vboo.attribute('title').select()
    #builder.select(titleAttr)
    
    catAttr = catv.attribute('category_name').select(groupBy=True)
    builder.select(catAttr, rbc)
    builder.select(catv.attribute('id').select(visible=False, orderBy=True))
    pubAttr = vpub.attribute('name').select(visible=False)
    builder.select(pubAttr, rbp)
    
    citAttr = citv.attribute('city_name').select(condition=equal('Wolsztyn'), visible=False)
    builder.select(citAttr, rpc)
    
    

    
    print builder.build()
    
main()
