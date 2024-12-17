from app import app, db, Product

with app.app_context():
    featured_products = Product.query.filter_by(is_featured=True).all()
    print("Featured Products:")
    for product in featured_products:
        print(f"- {product.name}")
