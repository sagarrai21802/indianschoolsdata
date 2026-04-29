<?php

namespace App\Http\Controllers;

use App\Models\School;
use Illuminate\Http\Request;

class InquiryController extends Controller
{
    public function create(string $city, string $school)
    {
        $school = School::with('city')
            ->where('slug', $school)
            ->whereHas('city', fn ($q) => $q->where('slug', $city))
            ->firstOrFail();

        return view('pages.inquiry.create', compact('school'));
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'school_id' => 'required|exists:schools,id',
            'parent_name' => 'required|string|max:255',
            'email' => 'required|email|max:255',
            'phone' => 'required|string|max:20',
            'child_name' => 'nullable|string|max:255',
            'child_grade' => 'nullable|string|max:50',
            'message' => 'nullable|string|max:1000',
        ]);

        // Here you would typically save to database or send email
        // For now, just redirect with success message

        return redirect()->back()->with('success', 'Your inquiry has been submitted. The school will contact you soon.');
    }
}
