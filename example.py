from views import View, Relation, AttrPair, Schema
from pyqube import QueryBuilder, aggrCount, lesser, greater

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
    
    subBuilder = QueryBuilder(schema)
    authorAttr = booksView.attribute('author').select(aggregate=aggrCount, altName='Authors')
    subBuilder.select(authorAttr)
    
    categoryAttr = categoriesView.attribute('category_name').select(groupBy=True)
    subBuilder.select(categoryAttr)
    
    yearAttr = booksView.attribute('year').select(condition=lesser(), orderBy=True, groupBy=True)
    subBuilder.select(yearAttr)
    
    year2Attr = booksView.attribute('year').select(visible=False, condition=greater())
    subBuilder.select(year2Attr)
    
    publisherIdAttr = booksView.attribute('publisher').select(groupBy=True)
    subBuilder.select(publisherIdAttr)
    
    subView = subBuilder.createView('AuthorsView')
    
    authorsPublisher = Relation(
                                [AttrPair
                                    (
                                        subView.attribute('publisher'),
                                        publishersView.attribute('id')
                                    )
                                ]
                                )
    schema.addView(subView, authorsPublisher)
 
    builder = QueryBuilder(schema)
    builder.select(subView.attribute('Authors').select( condition=greater()) )
    builder.select(publishersView.attribute('name').select())
    
    print builder.build()
    
if __name__ == '__main__':
    main()
