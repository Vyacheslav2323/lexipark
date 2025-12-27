export default function Landing() {
    return (
      <div className="min-h-screen bg-white text-gray-900 flex flex-col items-center">
        {/* Hero */}
        <main className="max-w-6xl w-full px-6 pt-20 pb-28 text-center">
          <div className="max-w-3xl mx-auto">
            <h1 className="text-4xl md:text-6xl font-bold leading-tight">
            Learn your grammar.  
              <span className="block text-blue-600">Learn your vocabulary.</span>
            </h1>
  
            <p className="mt-6 text-2xl text-gray-600">
            Accurate translation with grammar explanations that adapt to your personal learning history. No noise. No overload.
            </p>
  
            <div className="mt-10 flex gap-4 justify-center">
              <a
                href="/translator"
                className="inline-flex items-center justify-center rounded-lg
                           bg-blue-600 px-6 py-3 text-white font-medium
                           hover:bg-blue-700 transition"
              >
                Try the Translator
              </a>
  
              <a
                href="#example"
                className="inline-flex items-center justify-center rounded-lg
                           border border-gray-300 px-6 py-3 text-gray-700
                           hover:bg-gray-50 transition"
              >
                See Grammar Example
              </a>
            </div>
          </div>
        </main>
  
        {/* Example */}
        <section
          id="example"
          className="bg-gray-50 border-t border-gray-200 w-full"
        >
          <div className="max-w-6xl mx-auto px-6 py-20 text-center">
            <h2 className="text-2xl font-semibold mb-10">
              Example
            </h2>
  
            <div className="grid md:grid-cols-2 gap-8">
              {/* Input */}
              <div className="rounded-xl bg-white p-6 border">
                <div className="text-sm text-gray-500 mb-2">Input</div>
                <p className="text-lg font-medium">
                  What's this?
                </p>
                <div className="text-sm text-gray-500 mb-2">Response</div>
                <p className="text-lg font-medium">
                  이거 뭐야?
                </p>
              </div>
  
              {/* Output */}
              <div className="rounded-xl bg-white p-6 border">
                <div className="text-sm text-gray-500 mb-2">Explanation</div>
                <p className="text-sm text-gray-700 leading-relaxed">
                  <span className="font-semibold">Noun + (이)야</span>  
                  <br />
                  Used in informal speech to ask about identity or nature.
                  Equivalent to “What is it?”  
                  <br />
                  <br />
                  Not used in polite or formal contexts.
                </p>
              </div>
            </div>
          </div>
        </section>
  
        {/* Footer CTA */}
        <footer className="border-t border-gray-200 w-full">
          <div className="max-w-6xl mx-auto px-6 py-16 flex flex-col md:flex-row
                          items-center justify-center gap-6 text-center">
            <p className="text-gray-600">
              Built for learners who want understanding, not just translation.
            </p>
  
            <a
              href="/translator"
              className="inline-flex items-center justify-center rounded-lg
                         bg-blue-600 px-6 py-3 text-white font-medium
                         hover:bg-blue-700 transition"
            >
              Start Translating
            </a>
          </div>
        </footer>
      </div>
    );
  }
  