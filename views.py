class Schema(object):
    '''
        Database schema, which includes views (tables and predefined queries)
        and theirs relations.
    '''
    def __init__(self):
        self.views = {} 
        self.rels = {}
        
    def addView(self, view, relation=None):
        '''
            Adds view to schema.
            params:
                - view: view to add
                - relation: optional relation of added view and
                other view already existing in schema. If relation
                is passed and related view does not exist, an exception is raised.
        '''
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
        '''
            Finds all views, which have relation with passed one.
        '''
        return self.views[view]
        
    def relation(self, view, related):
        '''
            Finds object representing relation between two views.
            If such relation is not fount, method returns None.
            params:
                - view: table or query
                - related: table or query, which is related to view
        '''
        if self.rels.has_key((view, related)):
            return self.rels[(view, related)]
        elif self.rels.has_key((related, view)):
            return self.rels[(related, view)]
        return None
        
class ViewAttr(object):
    '''
        Attribute of view. This class is used to define views in database
        schema. It is cloned for each specific query.
    '''
    def __init__(self, name, view):
        self.name = name
        self.view = view 
        
    def select(self, visible=True, orderBy=False, groupBy=False, condition=None, aggregate=None, altName=None):
        '''
            Uses parameters and creates attribute used in SELECT clause
            parmas:
                - visible: if true view attribute is visible in SELECt clause.
                - orderBy: if true view attribute is used to order selected rows.
                - groupBy: if true view attribute is used to group aggregated values
                - condition: function used to create conditonal expression in query
                - aggregate: aggregation function
                - altName: alternative (alias) name for attribute
        '''
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
    '''
        Cloned version of view attributed. It represents properties of view attribute
        specific for builded query.
    '''
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
        return str(self)
    
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
    '''
        Represents table in database or predefined query,
        which might be used as subquery.
    '''
    
    def __init__(self, src, name, attrNames):
        '''
            Initialise new view. 
            params:
                - src: definition of view (table name, select query) used to build query.
                - name: humand friendly name of view.
                - attrNames: names of attributes.
        '''
        self.src = src
        self.attrs = {}
        for n in attrNames:
            self.attrs[n] = ViewAttr(n, self)
        self.name = name    
    
    def attribute(self, name):
        '''
            Finds attribute in view by passed name.
        '''
        return self.attrs[name]
        
    def __str__(self):
        return self.src
        
    def __repr__(self):
        return self.src

class Condition(object):
    '''
        Conditional expression used in WHERE clause
    '''
    
    def __init__(self, fmt, value=None):
        '''
            Initialise expresion
            params:
                - fmt: format string used to create string used in WHERE clause
                - value: (optional) value used in condition. If None placeholder '?' is used instead.
        '''
        self.fmt = fmt
        self.value = value
        
    def __str__(self):
        if self.value:
            return self.fmt % self.value
        else:
            return self.fmt % '?'
            
class Aggregate(object):
    '''
        Aggregation function.
    '''
    def __init__(self, name, attr):
        '''
            Initialise aggregation function
            params:
                - name: function's name
                - attr: SelectAttribute used with this funcion
        '''
        self.name = name
        self.attr = attr
        
    def __str__(self):
        return '%s( %s )' % (self.name, self.attr)
        
class Relation(object):
    '''
        Representation of relation between two views. Each relations contains
        one or more pairs of attributes.
    '''
    def __init__(self, pairs):
        '''
            Initialise relation with pairs of attributes.
        '''
        self.pairs = pairs
        
    def related(self, view):
        '''
            Finds related view.
        '''
        return self.pairs[0].related(view)
        
    def toString(self, vleft, vright):
        '''
            Creates string representation of relation used in JOIN part of query.
        '''
        return ' AND '.join([p.toString(vleft, vright) for p in self.pairs])
        
    def __str__(self):
        return '%s %s' %(self.pairs[0].left, self.pairs[0].right)
        
class AttrPair(object):

    '''
        Pair of attributes which defines part of relation of 
        two views.
    '''
    def __init__(self, leftAttr, rightAttr):
        '''
            Initialize new pair of attributes.
            params:
                - leftAttr: attribute from first view.
                - rightAttr: attribute from view related to first one.
        '''
        self.left = leftAttr
        self.right = rightAttr
        
    def related(self, view):
        '''
            Finds view related to passed one. Choice is based on
            attributes in this pair.
        '''
        if self.left.view == view:
            return self.right
        elif self.right.view == view:
            return self.left
        else:
            return None
    
    def attribute(self, view):
        '''
            Finds matching attribute from view related to passed one.
            If pairs does not define relation for view, exception is raised.
        '''
        if view == self.left.view:
            return self.left
        elif view == self.right.view:
            return self.right
        else:
            raise Exception('Views do not match')
            
    def toString(self, vleft, vright):
        '''
            Creates string representation of pair used in JOIN part of query.
        '''
        a = vleft.alias+'.'+self.attribute(vleft.view).name
        b = vright.alias+'.'+self.attribute(vright.view).name
        return a+' = '+b
