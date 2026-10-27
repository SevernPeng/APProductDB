from django.test import SimpleTestCase

from catalog.management.commands.sync_official_accessory_images import parse_product_cards


class ParseOfficialAccessoryCardsTests(SimpleTestCase):
    def test_extracts_model_global_page_and_default_image(self):
        html = '''
        <li class="tp-product-item" data-id="1">
          <img class="tp-hidden tp-product-default tp-product-center"
               data-src="https://static.tp-link.com/upload/image-header/POE380S.png">
          <a class="ga-click tp-product-link" aria-label="POE380S"
             href="/en/business-networking/omada-accessory-power-poe/poe380s/">&nbsp;</a>
        </li>
        '''
        cards = parse_product_cards(html)
        self.assertEqual(
            cards["poe380s"],
            {
                "model": "POE380S",
                "page_url": "https://www.omadanetworks.com/en/business-networking/omada-accessory-power-poe/poe380s/",
                "image_url": "https://static.tp-link.com/upload/image-header/POE380S.png",
            },
        )
