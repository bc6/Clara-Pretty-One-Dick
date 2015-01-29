#Embedded file name: markdown\etree_loader.py


def importETree():
    """Import the best implementation of ElementTree, return a module object."""
    etree_in_c = None
    try:
        import xml.etree.cElementTree as etree_in_c
        from xml.etree.ElementTree import Comment
    except ImportError:
        try:
            import xml.etree.ElementTree as etree
        except ImportError:
            try:
                import cElementTree as etree_in_c
                from elementtree.ElementTree import Comment
            except ImportError:
                try:
                    import elementtree.ElementTree as etree
                except ImportError:
                    raise ImportError('Failed to import ElementTree')

    if etree_in_c:
        if etree_in_c.VERSION < '1.0.5':
            raise RuntimeError('cElementTree version 1.0.5 or higher is required.')
        etree_in_c.test_comment = Comment
        return etree_in_c
    if etree.VERSION < '1.1':
        raise RuntimeError('ElementTree version 1.1 or higher is required')
    else:
        return etree
