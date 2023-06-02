
#include <iostream>
#include <string>


#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include "rapidjson/ostreamwrapper.h"

#include "game.hpp"

using namespace std;


int main(int argc, char *argv[]) {

    // argv = ["filename", "test"] if unittesting
    // argv = ["filename"]         if not unittesting

    string line;
    rapidjson::StringBuffer buffer;
    rapidjson::Document doc;
    rapidjson::OStreamWrapper streamOut(cout);
    rapidjson::Writer<rapidjson::OStreamWrapper> writer;

    const bool isUnitTesting = argc > 1 && strcmp(argv[1], "test") == 0;
    Game game(isUnitTesting);

    while (1) {
        getline(cin, line);
        if (line == "quit") {
            break;
        }
        doc.Parse(line.c_str());
        if (doc.HasParseError()) {
            cout << "{\"error\":\"JSON parse failed\"}\n";
            continue;
        }

        writer.Reset(streamOut);
        doc.Accept(writer);
        cout << "\n";
    }
    return 0;
}
