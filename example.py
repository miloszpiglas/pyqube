from views import *
from pyqube import *

def main():
    booksView = View('books', 'Books', ['title', 'author', 'year', 'publisher', 'category'])
    publishersView = View('publishers', 'Publishers', ['id', 'name', 'city'])
    categoriesView = View('categories', 'Categories', ['id', 'category_name'])
    citiesView = View('cities', 'Cities', ['id', 'city_name'])
    
    bookPublisher = Relation(
                            [AttrPair
                                (booksView['publisher'], 
                                            publishersView['id']
                                )
                            ]
                            )
    publisherCity = Relation(
                            [AttrPair
                                (
                                    publishersView['city'], 
                                    citiesView['id']
                                )
                            ]
                            )
    bookCategory = Relation(
                           [AttrPair
                                (
                                    booksView['category'], 
                                    categoriesView['id']
                                )
                            ]
                            )
    schema = Schema()
    schema.addView(booksView)
    schema.addView(publishersView, bookPublisher)
    schema.addView(categoriesView, bookCategory)
    schema.addView(citiesView, publisherCity)
    
    schema.attrByName('Categories.category_name').userName = 'Category name'
    
    subBuilder = QueryBuilder(schema)
    authorAttr = booksView['author'].select(aggregate=lambda a: 'count('+a+')', altName='Authors', orderBy=True)
    subBuilder.add(authorAttr)
    
    categoryAttr = categoriesView['category_name'].select(groupBy=True, orderBy=True)
    subBuilder.add(categoryAttr)
    
    publisherIdAttr = booksView['publisher'].select(groupBy=True, condition=andCondition('LIKE '))
    subBuilder.add(publisherIdAttr)
    
    yearChain = ConditionChain()
    yc = yearChain.addOr('=').addOr('=').addOr('=').build()
    
    yearAttr = booksView['year'].select(condition=yc, orderBy=True, groupBy=True)
    subBuilder.add(yearAttr)
    
    #year2Attr = booksView.attribute('year').select(visible=False, condition=GT)
    #subBuilder.select(year2Attr)
    
    
    subView = subBuilder.createQuery('AuthorsView')
    
    authorsPublisher = Relation(
                                [AttrPair
                                    (
                                        subView['publisher'],
                                        publishersView['id']
                                    )
                                ]
                                )
                                
    schema.addView(subView, authorsPublisher)
    sa = schema.attributes()
    
    print sa[0], sa[0].view.source
    print sa[-1], sa[-1].view.source
    
    builder = QueryBuilder(schema)
    builder.add(subView['Authors'].select(condition=orCondition('=')) )
    builder.add(publishersView['name'].select(), outerJoin=True)
    
    prepSub = subView.prepare()
    print prepSub.statement
    print prepSub.params
    print prepSub.attributes
    print
    prepMain = builder.build()
    print prepMain.statement
    print prepMain.params
    print prepMain.attributes
    
    
if __name__ == '__main__':
    main()
