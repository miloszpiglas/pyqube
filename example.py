from views import *
from pyqube import *

def main():
    booksView = View('books', 'Books', ['title', 'author', 'year', 'publisher', 'category'])
    publishersView = View('publishers', 'Publishers', ['id', 'name', 'city'])
    categoriesView = View('categories', 'Categories', ['id', 'category_name'])
    citiesView = View('cities', 'Cities', ['id', 'city_name'])
    
    bookPublisher = Relation(
                            [AttrPair
                                (booksView.attribute('publisher'), 
                                            publishersView.attribute('id')
                                )
                            ]
                            )
    publisherCity = Relation(
                            [AttrPair
                                (
                                    publishersView.attribute('city'), 
                                    citiesView.attribute('id')
                                )
                            ]
                            )
    bookCategory = Relation(
                           [AttrPair
                                (
                                    booksView.attribute('category'), 
                                    categoriesView.attribute('id')
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
    authorAttr = booksView.attribute('author').select(aggregate=lambda a: 'count('+a+')', altName='Authors')
    subBuilder.select(authorAttr)
    
    categoryAttr = categoriesView.attribute('category_name').select(groupBy=True)
    subBuilder.select(categoryAttr)
    
    yearChain = ConditionChain()
    yc = yearChain.addOr('=').addOr('=').addOr('=').build()
    
    yearAttr = booksView.attribute('year').select(condition=yc, orderBy=True, groupBy=True)
    subBuilder.select(yearAttr)
    
    #year2Attr = booksView.attribute('year').select(visible=False, condition=GT)
    #subBuilder.select(year2Attr)
    
    publisherIdAttr = booksView.attribute('publisher').select(groupBy=True, condition=andCondition('LIKE '))
    subBuilder.select(publisherIdAttr)
    
    subView = subBuilder.createQuery('AuthorsView')
    
    authorsPublisher = Relation(
                                [AttrPair
                                    (
                                        subView.attribute('publisher'),
                                        publishersView.attribute('id')
                                    )
                                ]
                                )
                                
    schema.addView(subView, authorsPublisher)
    sa = schema.attributes()
    
    print sa[0], sa[0].view.source
    print sa[-1], sa[-1].view.source
    
    builder = QueryBuilder(schema)
    builder.select(subView.attribute('Authors').select(condition=orCondition('=')) )
    builder.select(publishersView.attribute('name').select())
    
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
