

from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Folder where uploaded product images will be stored
UPLOAD_FOLDER = os.path.join("static", "images")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Create folder automatically if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Allowed image formats
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def load_products():

    # Read Excel without assuming a header row
    df = pd.read_excel("pricelist.xlsx", header=None)

    products = []
    current_category = None

    for _, row in df.iterrows():

        # Your Excel data is in these columns
        sno = row.iloc[2]
        name = row.iloc[3]
        pack = row.iloc[4]
        price = row.iloc[5]

        # Skip empty rows
        if (
            pd.isna(sno)
            and pd.isna(name)
            and pd.isna(pack)
            and pd.isna(price)
        ):
            continue

        # Detect category rows
        if isinstance(sno, str) and pd.isna(name):

            category_name = sno.strip()

            if category_name.lower() not in [
                "sno.",
                "sno"
            ]:
                current_category = category_name

            continue

        # Skip header
        if str(sno).strip().lower() in [
            "sno.",
            "sno"
        ]:
            continue

        # Add actual products
        if pd.notna(sno) and pd.notna(name):

            try:
                price_value = float(price)
            except:
                price_value = 0

            # Create unique product ID using Excel row number
            product_id = len(products) + 1

            products.append({

                "id": product_id,

                "category": current_category or "Other",

                "sno": str(sno),

                "name": str(name).strip(),

                "pack": (
                    ""
                    if pd.isna(pack)
                    else str(pack).strip()
                ),

                "price": price_value

            })

    return products


@app.route("/")
def home():

    products = load_products()

    # Check whether an image exists for every product
    for product in products:

        image_found = None

        for extension in ["jpg", "jpeg", "png", "webp"]:

            image_name = f"{product['id']}.{extension}"

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                image_name
            )

            if os.path.exists(image_path):

                image_found = image_name
                break

        product["image"] = image_found

    return render_template(
        "index.html",
        products=products
    )


# ==================================================
# ADMIN IMAGE UPLOAD PAGE
# ==================================================

@app.route("/admin/images")
def admin_images():

    products = load_products()

    # Find existing images
    for product in products:

        image_found = None

        for extension in ["jpg", "jpeg", "png", "webp"]:

            image_name = f"{product['id']}.{extension}"

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                image_name
            )

            if os.path.exists(image_path):

                image_found = image_name
                break

        product["image"] = image_found

    return render_template(
        "admin_images.html",
        products=products
    )


# ==================================================
# UPLOAD IMAGE FOR A SPECIFIC PRODUCT
# ==================================================

@app.route("/upload-image/<int:product_id>", methods=["POST"])
def upload_image(product_id):

    if "image" not in request.files:
        return redirect(url_for("admin_images"))

    file = request.files["image"]

    if file.filename == "":
        return redirect(url_for("admin_images"))

    if file and allowed_file(file.filename):

        # Get file extension
        extension = file.filename.rsplit(".", 1)[1].lower()

        # Delete old image if it exists
        for old_extension in ["jpg", "jpeg", "png", "webp"]:

            old_file = os.path.join(
                app.config["UPLOAD_FOLDER"],
                f"{product_id}.{old_extension}"
            )

            if os.path.exists(old_file):
                os.remove(old_file)

        # Save using product ID
        filename = f"{product_id}.{extension}"

        file.save(
            os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )
        )

    return redirect(url_for("admin_images"))


if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )

