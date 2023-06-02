
#ifndef BASE_MODELS_H
#define BASE_MODELS_H

#include <string>

using namespace std;

class BaseModel
{
    protected:
        string id;

    public:
        string getId();
        BaseModel();
};


#endif