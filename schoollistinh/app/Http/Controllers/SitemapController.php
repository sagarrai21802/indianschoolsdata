<?php

namespace App\Http\Controllers;

use App\Models\City;
use App\Models\School;
use Illuminate\Http\Response;

class SitemapController extends Controller
{
    public function index(): Response
    {
        $xml = '<?xml version="1.0" encoding="UTF-8"?>';
        $xml .= '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">';

        // Home page
        $xml .= $this->addUrl(route('home'), '1.0', 'daily');

        // Cities index
        $xml .= $this->addUrl(route('schools.index'), '0.9', 'weekly');

        // Search page
        $xml .= $this->addUrl(route('search'), '0.8', 'weekly');

        // Static pages
        $xml .= $this->addUrl(route('about'), '0.5', 'monthly');
        $xml .= $this->addUrl(route('contact'), '0.5', 'monthly');

        // City pages
        $cities = City::active()->withSchools()->get();
        foreach ($cities as $city) {
            $xml .= $this->addUrl(
                route('city.show', $city->slug),
                '0.8',
                'daily',
                $city->updated_at
            );
        }

        // School detail pages
        $schools = School::active()
            ->with('city')
            ->select('id', 'slug', 'city_id', 'updated_at')
            ->get();
        
        foreach ($schools as $school) {
            $xml .= $this->addUrl(
                route('school.show', [
                    'city' => $school->city->slug,
                    'school' => $school->slug
                ]),
                '0.6',
                'weekly',
                $school->updated_at
            );
        }

        $xml .= '</urlset>';

        return response($xml, 200, [
            'Content-Type' => 'application/xml',
        ]);
    }

    private function addUrl(string $url, string $priority, string $changefreq, ?\DateTimeInterface $lastmod = null): string
    {
        $xml = '<url>';
        $xml .= '<loc>' . htmlspecialchars($url) . '</loc>';
        
        if ($lastmod) {
            $xml .= '<lastmod>' . $lastmod->format('Y-m-d') . '</lastmod>';
        }
        
        $xml .= '<changefreq>' . $changefreq . '</changefreq>';
        $xml .= '<priority>' . $priority . '</priority>';
        $xml .= '</url>';

        return $xml;
    }
}
