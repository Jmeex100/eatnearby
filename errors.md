
    <!-- Fast Food Section -->
    <div class="mt-12">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">Fast Food</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            {% for item in fast_foods %}
            <div class="relative bg-white shadow-md rounded-lg overflow-hidden transform hover:scale-105 transition-transform duration-300">
                <img src="{{ item.image_url }}" alt="{{ item.name }}" class="w-full h-48 object-cover">
                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 opacity-0 hover:opacity-100 transition-opacity duration-300" style="pointer-events: none;">
                    <a href="javascript:void(0)" class="text-white text-lg font-semibold hover:underline" style="pointer-events: auto;" 
                       data-product-id="{{ item.product_id }}"
                       data-name="{{ item.name }}" 
                       data-price="{{ item.price }}" 
                       data-description="{{ item.description }}" 
                       onclick="openModal(event, this)">Order This</a>
                </div>
                <div class="p-6">
                    <h2 class="text-xl font-bold text-gray-800 mb-2">{{ item.name }}</h2>
                    <p class="text-gray-700 mb-4">{{ item.description }}</p>
                    <p class="text-red-600 font-semibold">Price: K{{ item.price }}</p>
                    <div class="text-center mt-4">
                        <a href="{% url 'order' item.product_id 'fastfood' %}" class="inline-block bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 transition duration-300">Order Now</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Food Section -->
    <div class="mt-12">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">Food</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            {% for item in foods %}
            <div class="relative bg-white shadow-md rounded-lg overflow-hidden transform hover:scale-105 transition-transform duration-300">
                <img src="{{ item.image_url }}" alt="{{ item.name }}" class="w-full h-48 object-cover">
                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 opacity-0 hover:opacity-100 transition-opacity duration-300" style="pointer-events: none;">
                    <a href="javascript:void(0)" class="text-white text-lg font-semibold hover:underline" style="pointer-events: auto;" 
                       data-product-id="{{ item.product_id }}"
                       data-name="{{ item.name }}" 
                       data-price="{{ item.price }}" 
                       data-description="{{ item.description }}" 
                       onclick="openModal(event, this)">Order This</a>
                </div>
                <div class="p-6">
                    <h2 class="text-xl font-bold text-gray-800 mb-2">{{ item.name }}</h2>
                    <p class="text-gray-700 mb-4">{{ item.description }}</p>
                    <p class="text-red-600 font-semibold">Price: K{{ item.price }}</p>
                    <div class="text-center mt-4">
                        <a href="{% url 'order' item.product_id 'food' %}" class="inline-block bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 transition duration-300">Order Now</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Drinks Section -->
    <div class="mt-12">
        <h2 class="text-2xl font-bold text-gray-800 mb-6">Drinks</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            {% for item in drinks %}
            <div class="relative bg-white shadow-md rounded-lg overflow-hidden transform hover:scale-105 transition-transform duration-300">
                <img src="{{ item.image_url }}" alt="{{ item.name }}" class="w-full h-48 object-cover">
                <div class="absolute inset-0 flex items-center justify-center bg-black bg-opacity-50 opacity-0 hover:opacity-100 transition-opacity duration-300" style="pointer-events: none;">
                    <a href="javascript:void(0)" class="text-white text-lg font-semibold hover:underline" style="pointer-events: auto;" 
                       data-product-id="{{ item.product_id }}"
                       data-name="{{ item.name }}" 
                       data-price="{{ item.price }}" 
                       data-description="{{ item.description }}" 
                       onclick="openModal(event, this)">Order This</a>
                </div>
                <div class="p-6">
                    <h2 class="text-xl font-bold text-gray-800 mb-2">{{ item.name }}</h2>
                    <p class="text-gray-700 mb-4">{{ item.description }}</p>
                    <p class="text-red-600 font-semibold">Price: K{{ item.price }}</p>
                    <div class="text-center mt-4">
                        <a href="{% url 'order' item.product_id 'drink' %}" class="inline-block bg-red-500 text-white px-4 py-2 rounded-md hover:bg-red-600 transition duration-300">Order Now</a>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
