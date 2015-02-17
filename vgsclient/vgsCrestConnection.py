#Embedded file name: vgsclient\vgsCrestConnection.py
import collections
import logging
Product = collections.namedtuple('Product', ['id', 'name', 'href'])
Offer = collections.namedtuple('Offer', ['id',
 'name',
 'description',
 'href',
 'price',
 'basePrice',
 'imageUrl',
 'productQuantities',
 'categories',
 'label'])
Category = collections.namedtuple('Category', ['id',
 'name',
 'href',
 'parentId',
 'subcategories',
 'tagIds'])
Label = collections.namedtuple('Label', ['name', 'description', 'url'])
AUR_CURRENCY = 'EAR'
PAYMENT_METHOD = 2
log = logging.getLogger(__name__)

class VgsCrestConnection:
    """
    A connection to the remote Crest VGS endpoint, in the context of the current user session
    """

    def __init__(self, storeName, crestConnectionService):
        self.storeName = storeName
        self.crestConnectionService = crestConnectionService
        self.store = None
        self.vgsRoot = None

    def ClearCache(self):
        self.store = None
        self.vgsRoot = None

    def _GetUserSession(self):
        return self.crestConnectionService.GetUserSession()

    def _GetVgsRoot(self):
        """
        Get the root resource of the vgs store
        """
        if self.vgsRoot is None:
            userSession = self._GetUserSession()
            server = userSession.Get(userSession.server, accept='vnd.ccp.eve.Api-v3')
            root = userSession.Get(server['virtualGoodStore']['href'], accept='vnd.ccp.eve.VgsRootLinkCollection-v1')
            self.vgsRoot = {x['name']:{'href': x['href']} for x in root}
        return self.vgsRoot

    def _GetVgsStore(self):
        """ Get the JSON object describing the current store """
        if self.store is None:
            userSession = self._GetUserSession()
            stores = userSession.Get(self._GetVgsRoot()['stores']['href'], accept='vnd.ccp.eve.VgsStoreCollection-v1')
            for store in stores:
                if store['name'] == self.storeName:
                    self.store = userSession.Get(store['href'], accept='vnd.ccp.eve.VgsStore-v1')
                    break

        return self.store

    def GetAurAccount(self):
        """ Get the JSON object describing the user's Aurum account """
        accounts = self._GetUserSession().Get(self._GetVgsRoot()['accounts']['href'], accept='vnd.ccp.eve.VgsAccountCollection-v1')
        for account in accounts:
            if account['currency'] == AUR_CURRENCY:
                return self._GetUserSession().Get(account['href'], accept='vnd.ccp.eve.VgsAccount-v1')

    def GetProducts(self):
        """
        Return a list of all products available in the default store.
        """
        return [ CreateProductFromJson(productJson) for productJson in self._GetProductsJson() ]

    def _GetProductsJson(self):
        """
        Return a list of all products available in the default store. Each product is a JSON object.
        """
        log.debug('_GetProductsJson')
        acceptSchema = 'vnd.ccp.eve.VgsProductCollection-v1'
        store = self._GetVgsStore()
        productCollection = self._GetUserSession().Get(store['products']['href'], accept=acceptSchema)
        log.debug('_GetProductsJson - Received page %s of %s' % (productCollection['currentPage'], productCollection['pageCount']))
        products = productCollection['items']
        while 'next' in productCollection:
            productCollection = self._GetUserSession().Get(productCollection['next']['href'], accept=acceptSchema)
            log.debug('_GetProductsJson - Received page %s of %s' % (productCollection['currentPage'], productCollection['pageCount']))
            products += productCollection['items']

        return products

    def GetProduct(self, productHref):
        """ Get the JSON object describing a product """
        return self._GetUserSession().Get(productHref, accept='vnd.ccp.eve.VgsProduct-v1')

    def GetOffers(self):
        """
        Return a list of all offers from the vgs in our default store, ignoring any offers with no products.
        """
        return [ CreateOfferFromJson(offerJson) for offerJson in self._GetOffersJson() if 'products' in offerJson and len(offerJson['products']) ]

    def GetOfferPage(self, userSession, href, acceptSchema):
        offerCollection = userSession.Get(href, accept=acceptSchema)
        log.debug('GetOfferPage - Received page %s of %s' % (offerCollection['currentPage'], offerCollection['pageCount']))
        return offerCollection

    def _GetOffersJson(self):
        """
        Return a list of all offers from the vgs in our default store. Each offer is a JSON object.
        """
        log.debug('_GetOffersJson')
        userSession = self._GetUserSession()
        store = self._GetVgsStore()
        acceptSchema = 'vnd.ccp.eve.VgsOfferCollection-v2'
        offerCollection = self.GetOfferPage(userSession, store['offers']['href'], acceptSchema)
        offers = offerCollection['items']
        while 'next' in offerCollection:
            offerCollection = self.GetOfferPage(userSession, offerCollection['next']['href'], acceptSchema)
            offers += offerCollection['items']

        return offers

    def GetOffer(self, offerUri):
        """ Get the JSON object describing an offer """
        return self._GetUserSession().Get(offerUri)

    def BuyOffer(self, offer, qty = 1):
        """
        Tries to buy an offer from the store, using the current user session
        """
        root = self._GetVgsRoot()
        store = self._GetVgsStore()
        sale = {'storeId': store['id'],
         'currency': AUR_CURRENCY,
         'paymentMethodId': PAYMENT_METHOD,
         'saleLines': [{'offerId': offer.id,
                        'offerQuantity': qty}]}
        response = self._GetUserSession().Post(root['sales']['href'], payload=sale, content='vnd.ccp.eve.VgsSale-v1', header=True)
        return response

    def GetSales(self, salesUri = None):
        """
        returns the sales for the user session , returns a json object
        Only returns one page , ui is responsible to ask for the correct page,
        if no page is specified the first paqe is returned
        """
        if salesUri:
            uri = salesUri
        else:
            root = self._GetVgsRoot()
            uri = root['sales']['href']
        return self._GetUserSession().Get(uri, accept='vnd.ccp.eve.VgsSaleCollection-v1')

    def GetSale(self, saleUri):
        """
        return a specific sale, returns a json object describing the sale
        """
        return self._GetUserSession().Get(saleUri, accept='vnd.ccp.eve.VgsSale-v1')

    def GetCategories(self):
        return [ CreateCategoryFromJson(categoryJson) for categoryJson in self._GetCategories() ]

    def _GetCategories(self):
        """
        return the categories available in the store
        """
        store = self._GetVgsStore()
        categoryCollection = self._GetUserSession().Get(store['categories']['href'], accept='vnd.ccp.eve.VgsCategoryCollection-v1')
        categories = categoryCollection['items']
        while 'next' in categoryCollection:
            categoryCollection = self._GetUserSession().Get(categories['next'], accept='vnd.ccp.eve.VgsCategoryCollection-v1')
            categories += categoryCollection['items']

        return categories


def CreateProductFromJson(productJson):
    """ Return an Product instance created from a JSON description """
    return Product(productJson['id'], productJson['name'], productJson['href'])


def CreateOfferFromJson(offerJson):
    """ Return an Offer instance created from a JSON description """
    return Offer(offerJson['id'], offerJson['name'], offerJson['description'], offerJson['href'], offerJson['price'], offerJson['basePrice'], offerJson['imageUrl'], {product['id']:(product['typeId'], product['quantity']) for product in offerJson['products']}, {category['id'] for category in offerJson['categories']}, CreateLabelFromJson(offerJson['label']) if offerJson['label'] is not None else None)


def CreateCategoryFromJson(categoryJson):
    """ Return a Category instance create from a JSON object """
    return Category(categoryJson['id'], categoryJson['name'], categoryJson['href'], categoryJson['parent']['id'] if categoryJson['parent'] is not None else None, set(), set())


def CreateLabelFromJson(labelJson):
    return Label(labelJson['name'], labelJson['description'], labelJson['url'])
