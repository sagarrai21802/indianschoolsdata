<?php

namespace App\Http\Controllers;

use App\Models\City;
use App\Models\School;
use App\Repositories\SchoolRepository;

class ProgrammaticSeoController extends Controller
{
    private SchoolRepository $repository;

    public function __construct(SchoolRepository $repository)
    {
        $this->repository = $repository;
    }

    public function cbse(string $city)
    {
        return $this->renderBoardPage($city, 'cbse', 'CBSE');
    }

    public function icse(string $city)
    {
        return $this->renderBoardPage($city, 'icse', 'ICSE');
    }

    public function stateBoard(string $city)
    {
        return $this->renderBoardPage($city, 'state-board', 'State Board');
    }

    private function renderBoardPage(string $citySlug, string $boardSlug, string $boardName)
    {
        $city = $this->getCity($citySlug);
        if (!$city) {
            abort(404);
        }

        $schools = $this->getSchoolsByBoard($citySlug, $boardName);

        if ($schools->isEmpty()) {
            abort(404);
        }

        $seoConfig = config("school-seo.board_slugs.{$boardSlug}");

        return view('pages.seo.board', [
            'city' => $city,
            'schools' => $schools,
            'board' => $boardName,
            'seo' => $seoConfig,
        ]);
    }

    public function playSchool(string $city)
    {
        return $this->renderTypePage($city, 'play-school', 'Play School');
    }

    public function primary(string $city)
    {
        return $this->renderTypePage($city, 'primary', 'Primary');
    }

    public function secondary(string $city)
    {
        return $this->renderTypePage($city, 'secondary', 'Secondary');
    }

    public function seniorSecondary(string $city)
    {
        return $this->renderTypePage($city, 'senior-secondary', 'Senior Secondary');
    }

    private function renderTypePage(string $citySlug, string $typeSlug, string $typeName)
    {
        $city = $this->getCity($citySlug);
        if (!$city) {
            abort(404);
        }

        $schools = $this->getSchoolsByType($citySlug, $typeName);

        if ($schools->isEmpty()) {
            abort(404);
        }

        $seoConfig = config("school-seo.school_type_slugs.{$typeSlug}");

        return view('pages.seo.type', [
            'city' => $city,
            'schools' => $schools,
            'type' => $typeName,
            'seo' => $seoConfig,
        ]);
    }

    public function topRated(string $city)
    {
        $cityModel = $this->getCity($city);
        if (!$cityModel) {
            abort(404);
        }

        $schools = School::active()
            ->whereHas('city', fn ($q) => $q->where('slug', $city))
            ->minRating(4.0)
            ->orderByDesc('rating')
            ->limit(50)
            ->get();

        if ($schools->isEmpty()) {
            // Try repository
            $allSchools = $this->repository->getSchoolsByCity($city, 1, 1000)['schools'];
            $schools = $allSchools->filter(fn ($s) => ($s['rating'] ?? 0) >= 4.0)->sortByDesc('rating');
        }

        return view('pages.seo.top-rated', [
            'city' => $cityModel,
            'schools' => $schools,
        ]);
    }

    private function getCity(string $slug)
    {
        $city = City::where('slug', $slug)->first();
        
        if (!$city) {
            $cityData = $this->repository->getCity($slug);
            if ($cityData) {
                $city = (object) $cityData;
            }
        }

        return $city;
    }

    private function getSchoolsByBoard(string $citySlug, string $board)
    {
        $schools = School::active()
            ->whereHas('city', fn ($q) => $q->where('slug', $citySlug))
            ->byBoard($board)
            ->orderByDesc('rating')
            ->limit(50)
            ->get();

        if ($schools->isEmpty()) {
            $allSchools = $this->repository->getSchoolsByCity($citySlug, 1, 1000)['schools'];
            $schools = $allSchools->filter(fn ($s) => ($s['board'] ?? '') === $board)->sortByDesc('rating');
        }

        return $schools;
    }

    private function getSchoolsByType(string $citySlug, string $type)
    {
        $schools = School::active()
            ->whereHas('city', fn ($q) => $q->where('slug', $citySlug))
            ->where('school_type', 'like', "%{$type}%")
            ->orderByDesc('rating')
            ->limit(50)
            ->get();

        if ($schools->isEmpty()) {
            $allSchools = $this->repository->getSchoolsByCity($citySlug, 1, 1000)['schools'];
            $schools = $allSchools->filter(fn ($s) => str_contains($s['school_type'] ?? '', $type))->sortByDesc('rating');
        }

        return $schools;
    }
}
