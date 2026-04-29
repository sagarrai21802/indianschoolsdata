<?php

return [
    'board_slugs' => [
        'cbse' => [
            'label' => 'CBSE Schools',
            'title' => 'CBSE Schools in {city}',
            'meta_description' => 'Find CBSE schools in {city}: Central Board of Secondary Education affiliated schools with fees, reviews, and admission details.',
            'h1' => 'CBSE Schools in {city}',
            'intro' => 'Browse CBSE-affiliated schools in {city}. CBSE (Central Board of Secondary Education) is India\'s national board popular for its structured curriculum and nationwide acceptance.',
        ],
        'icse' => [
            'label' => 'ICSE Schools',
            'title' => 'ICSE Schools in {city}',
            'meta_description' => 'Find ICSE schools in {city}: Indian Certificate of Secondary Education affiliated schools with fees and reviews.',
            'h1' => 'ICSE Schools in {city}',
            'intro' => 'Browse ICSE-affiliated schools in {city}. ICSE (Indian Certificate of Secondary Education) is known for comprehensive curriculum and international recognition.',
        ],
        'state-board' => [
            'label' => 'State Board Schools',
            'title' => 'State Board Schools in {city}',
            'meta_description' => 'Find state board schools in {city} with affordable fees and regional language options.',
            'h1' => 'State Board Schools in {city}',
            'intro' => 'Browse state board schools in {city}. State boards offer affordable education with curriculum tailored to regional needs.',
        ],
    ],

    'school_type_slugs' => [
        'play-school' => [
            'label' => 'Play Schools',
            'title' => 'Play Schools in {city}',
            'meta_description' => 'Find play schools and preschools in {city} for early childhood education.',
            'h1' => 'Play Schools in {city}',
            'intro' => 'Browse play schools in {city} for children aged 2-5 years. Early childhood education builds foundation for lifelong learning.',
        ],
        'primary' => [
            'label' => 'Primary Schools',
            'title' => 'Primary Schools in {city}',
            'meta_description' => 'Find primary schools in {city} for grades 1-5 with best teaching methods.',
            'h1' => 'Primary Schools in {city}',
            'intro' => 'Browse primary schools in {city} for foundational education from grades 1 to 5.',
        ],
        'secondary' => [
            'label' => 'Secondary Schools',
            'title' => 'Secondary Schools in {city}',
            'meta_description' => 'Find secondary schools in {city} for grades 6-10 with board affiliations.',
            'h1' => 'Secondary Schools in {city}',
            'intro' => 'Browse secondary schools in {city} for middle and high school education from grades 6 to 10.',
        ],
        'senior-secondary' => [
            'label' => 'Senior Secondary Schools',
            'title' => 'Senior Secondary Schools in {city}',
            'meta_description' => 'Find senior secondary schools in {city} for grades 11-12 with science, commerce, arts streams.',
            'h1' => 'Senior Secondary Schools in {city}',
            'intro' => 'Browse senior secondary schools in {city} for grades 11-12 offering science, commerce, and humanities streams.',
        ],
    ],

    'fee_range_slugs' => [
        'under-50k' => ['min' => 0, 'max' => 50000, 'label' => 'Under ₹50,000 / year'],
        '50k-1lakh' => ['min' => 50000, 'max' => 100000, 'label' => '₹50,000–₹1,00,000 / year'],
        '1lakh-2lakh' => ['min' => 100000, 'max' => 200000, 'label' => '₹1,00,000–₹2,00,000 / year'],
        '2lakh-plus' => ['min' => 200000, 'max' => 9999999, 'label' => '₹2,00,000+ / year'],
    ],

    'rating_slugs' => [
        'top-rated' => ['min_rating' => 4.0, 'label' => 'Top Rated Schools'],
        '4-plus' => ['min_rating' => 4.0, 'label' => '4+ Star Rated'],
        '3-plus' => ['min_rating' => 3.0, 'label' => '3+ Star Rated'],
    ],
];
