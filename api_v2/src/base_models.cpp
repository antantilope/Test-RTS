
#include <iostream>
#include <string>
#include <sstream>

#include "base_models.hpp"
#include "uuid.hpp"
#include "warnings.hpp"


using namespace std;

BaseModel::BaseModel() {
    stringstream strstream;
    uuid::v4(strstream);

    W_IGNORE_START NO_WAGGREGATE_RETURN
    id = strstream.str();
    W_IGNORE_STOP
}

string BaseModel::getId() {
    return id;
}
